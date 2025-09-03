import logging
import os
from typing import Optional

import ckan.model as model
from ckan.common import _, current_user, g, request
from ckan.lib import helpers
from ckan.lib.uploader import get_uploader
from ckan.logic import get_action
from ckan.plugins import toolkit
from ckan.types import PUploader
from flask import Response, make_response, send_file
from werkzeug.datastructures import FileStorage

import ckanext.feedback.services.resource.comment as comment_service
import ckanext.feedback.services.resource.likes as likes_service
import ckanext.feedback.services.resource.summary as summary_service
import ckanext.feedback.services.resource.validate as validate_service
from ckanext.feedback.controllers.cookie import (
    get_like_status_cookie,
    get_repeat_post_limit_cookie,
    set_like_status_cookie,
    set_repeat_post_limit_cookie,
)
from ckanext.feedback.controllers.pagination import get_pagination_value
from ckanext.feedback.models.resource_comment import ResourceCommentCategory
from ckanext.feedback.models.session import session
from ckanext.feedback.models.types import ResourceCommentResponseStatus
from ckanext.feedback.services.common.check import (
    check_administrator,
    has_organization_admin_role,
)
from ckanext.feedback.services.common.config import FeedbackConfig
from ckanext.feedback.services.common.send_mail import send_email
from ckanext.feedback.services.recaptcha.check import is_recaptcha_verified

log = logging.getLogger(__name__)


class ResourceController:
    # Render HTML pages
    # resource_comment/<resource_id>
    @staticmethod
    def comment(
        resource_id,
        category='',
        content='',
        attached_image_filename: Optional[str] = None,
    ):
        approval = True
        resource = comment_service.get_resource(resource_id)
        if not isinstance(current_user, model.User):
            # if the user is not logged in, display only approved comments
            approval = True
        elif (
            has_organization_admin_role(resource.Resource.package.owner_org)
            or current_user.sysadmin
        ):
            # if the user is an organization admin or a sysadmin, display all comments
            approval = None

        page, limit, offset, _ = get_pagination_value('resource_comment.comment')

        comments, total_count = comment_service.get_resource_comments(
            resource_id, approval, limit=limit, offset=offset
        )

        categories = comment_service.get_resource_comment_categories()
        cookie = get_repeat_post_limit_cookie(resource_id)
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': resource.Resource.package_id}
        )
        g.pkg_dict = {'organization': {'name': resource.organization_name}}
        if not category:
            selected_category = ResourceCommentCategory.REQUEST.name
        else:
            selected_category = category

        return toolkit.render(
            'resource/comment.html',
            {
                'resource': resource.Resource,
                'pkg_dict': package,
                'categories': categories,
                'cookie': cookie,
                'selected_category': selected_category,
                'content': content,
                'attached_image_filename': attached_image_filename,
                'page': helpers.Page(
                    collection=comments,
                    page=page,
                    item_count=total_count,
                    items_per_page=limit,
                ),
            },
        )

    # resource_comment/<resource_id>/comment/new
    @staticmethod
    def create_comment(resource_id):
        package_name = request.form.get('package_name', '')
        category = None
        if content := request.form.get('comment-content', ''):
            category = request.form.get('category', '')
        if rating := request.form.get('rating', ''):
            rating = int(rating)
        attached_image_filename = request.form.get('attached_image_filename', None)
        if not (category and content):
            toolkit.abort(400)

        attached_image: FileStorage = request.files.get("attached_image")
        if attached_image:
            try:
                attached_image_filename = ResourceController._upload_image(
                    attached_image
                )
            except toolkit.ValidationError as e:
                helpers.flash_error(e.error_summary, allow_html=True)
                return ResourceController.comment(resource_id, category, content)
            except Exception as e:
                log.exception(f'Exception: {e}')
                toolkit.abort(500)

        # Admins (org-admin or sysadmin) skip reCAPTCHA unless forced
        force_all = toolkit.asbool(FeedbackConfig().recaptcha.force_all.get())
        admin_bypass = False
        if isinstance(current_user, model.User):
            try:
                _res = comment_service.get_resource(resource_id)
                admin_bypass = current_user.sysadmin or has_organization_admin_role(
                    _res.Resource.package.owner_org
                )
            except Exception:
                admin_bypass = current_user.sysadmin

        if (force_all or not admin_bypass) and not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return ResourceController.comment(
                resource_id, category, content, attached_image_filename
            )

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return ResourceController.comment(
                resource_id, category, content, attached_image_filename
            )

        if not rating:
            rating = None

        comment_service.create_resource_comment(
            resource_id, category, content, rating, attached_image_filename
        )
        summary_service.create_resource_summary(resource_id)

        session.commit()

        category_map = {
            ResourceCommentCategory.REQUEST.name: _('Request'),
            ResourceCommentCategory.QUESTION.name: _('Question'),
            ResourceCommentCategory.THANK.name: _('Thank'),
        }

        try:
            resource = comment_service.get_resource(resource_id)
            send_email(
                template_name=(
                    FeedbackConfig().notice_email.template_resource_comment.get()
                ),
                organization_id=resource.Resource.package.owner_org,
                subject=FeedbackConfig().notice_email.subject_resource_comment.get(),
                target_name=resource.Resource.name,
                category=category_map[category],
                content=content,
                url=toolkit.url_for(
                    'resource_comment.comment', resource_id=resource_id, _external=True
                ),
            )
        except Exception:
            log.exception('Send email failed, for feedback notification.')

        helpers.flash_success(
            _(
                'Your comment has been sent.<br>The comment will not be displayed until'
                ' approved by an administrator.'
            ),
            allow_html=True,
        )
        resp = make_response(
            toolkit.redirect_to(
                'resource.read', id=package_name, resource_id=resource_id
            )
        )
        resp_with_cookie = set_repeat_post_limit_cookie(resp, resource_id)

        return resp_with_cookie

    # resource_comment/<resource_id>/comment/suggested
    @staticmethod
    def suggested_comment(
        resource_id,
        category='',
        content='',
        rating='',
        attached_image_filename: Optional[str] = None,
    ):
        # softened = suggest_ai_comment(comment=content)
        softened = "a"

        context = {'model': model, 'session': session, 'for_view': True}

        resource = comment_service.get_resource(resource_id)
        package = get_action('package_show')(
            context, {'id': resource.Resource.package_id}
        )
        g.pkg_dict = {'organization': {'name': resource.organization_name}}

        if softened is None:
            return toolkit.render(
                'resource/expect_suggestion.html',
                {
                    'resource': resource.Resource,
                    'pkg_dict': package,
                    'selected_category': category,
                    'rating': rating,
                    'content': content,
                    'attached_image_filename': attached_image_filename,
                },
            )

        return toolkit.render(
            'resource/suggestion.html',
            {
                'resource': resource.Resource,
                'pkg_dict': package,
                'selected_category': category,
                'rating': rating,
                'content': content,
                'attached_image_filename': attached_image_filename,
                'softened': softened,
            },
        )

    # resource_comment/<resource_id>/comment/check
    @staticmethod
    def check_comment(resource_id):
        if request.method == 'GET':
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        category = None
        if content := request.form.get('comment-content', ''):
            category = request.form.get('category', '')
        if rating := request.form.get('rating', ''):
            rating = int(rating)
        attached_image_filename = request.form.get('attached_image_filename', None)
        if not (category and content):
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        attached_image: FileStorage = request.files.get("attached_image")
        if attached_image:
            try:
                attached_image_filename = ResourceController._upload_image(
                    attached_image
                )
            except toolkit.ValidationError as e:
                helpers.flash_error(e.error_summary, allow_html=True)
                return ResourceController.comment(resource_id, category, content)
            except Exception as e:
                log.exception(f'Exception: {e}')
                toolkit.abort(500)

        # Admins (org-admin or sysadmin) skip reCAPTCHA unless forced
        force_all = toolkit.asbool(FeedbackConfig().recaptcha.force_all.get())
        admin_bypass = False
        if isinstance(current_user, model.User):
            try:
                _res = comment_service.get_resource(resource_id)
                admin_bypass = current_user.sysadmin or has_organization_admin_role(
                    _res.Resource.package.owner_org
                )
            except Exception:
                admin_bypass = current_user.sysadmin

        if (force_all or not admin_bypass) and not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return ResourceController.comment(
                resource_id, category, content, attached_image_filename
            )

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return ResourceController.comment(
                resource_id, category, content, attached_image_filename
            )

        categories = comment_service.get_resource_comment_categories()
        resource = comment_service.get_resource(resource_id)
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': resource.Resource.package_id}
        )
        g.pkg_dict = {'organization': {'name': resource.organization_name}}

        if not request.form.get(
            'comment-suggested', False
        ) and FeedbackConfig().moral_keeper_ai.is_enable(
            resource.Resource.package.owner_org
        ):
            is_ai = True
            if is_ai:
                # if check_ai_comment(comment=content) is False:
                return ResourceController.suggested_comment(
                    resource_id=resource_id,
                    rating=rating,
                    category=category,
                    content=content,
                    attached_image_filename=attached_image_filename,
                )

        return toolkit.render(
            'resource/comment_check.html',
            {
                'resource': resource.Resource,
                'pkg_dict': package,
                'categories': categories,
                'selected_category': category,
                'rating': rating,
                'content': content,
                'attached_image_filename': attached_image_filename,
            },
        )

    # resource_comment/<resource_id>/comment/check/attached_image/<attached_image_filename>
    @staticmethod
    def check_attached_image(resource_id: str, attached_image_filename: str):
        attached_image_path = comment_service.get_attached_image_path(
            attached_image_filename
        )
        return send_file(attached_image_path)

    # resource_comment/<resource_id>/comment/approve
    @staticmethod
    @check_administrator
    def approve_comment(resource_id):
        ResourceController._check_organization_admin_role(resource_id)
        resource_comment_id = request.form.get('resource_comment_id')
        if not resource_comment_id:
            toolkit.abort(400)

        comment_service.approve_resource_comment(resource_comment_id, current_user.id)
        summary_service.refresh_resource_summary(resource_id)
        session.commit()

        return toolkit.redirect_to('resource_comment.comment', resource_id=resource_id)

    @staticmethod
    @check_administrator
    def approve_reply(resource_id):
        ResourceController._check_organization_admin_role(resource_id)
        reply_id = request.form.get('resource_comment_reply_id')
        if not reply_id:
            toolkit.abort(400)

        try:
            comment_service.approve_reply(reply_id, current_user.id)
            session.commit()
        except PermissionError:
            helpers.flash_error(
                _('Cannot approve reply before the parent comment is approved.'),
                allow_html=True,
            )
        except ValueError:
            toolkit.abort(404)
        return toolkit.redirect_to('resource_comment.comment', resource_id=resource_id)

    # resource_comment/<resource_id>/comment/reply
    @staticmethod
    def reply(resource_id):
        resource_comment_id = request.form.get('resource_comment_id', '')
        content = request.form.get('reply_content', '')
        if not (resource_comment_id and content):
            toolkit.abort(400)

        # Admins (org-admin or sysadmin) skip reCAPTCHA unless forced
        force_all = toolkit.asbool(FeedbackConfig().recaptcha.force_all.get())
        admin_bypass = False
        if isinstance(current_user, model.User):
            try:
                _res = comment_service.get_resource(resource_id)
                admin_bypass = current_user.sysadmin or has_organization_admin_role(
                    _res.Resource.package.owner_org
                )
            except Exception:
                admin_bypass = current_user.sysadmin

        # Reply permission control (admin or reply_open)
        reply_open = False
        try:
            reply_open = FeedbackConfig().resource_comment.reply_open.is_enable(
                _res.Resource.package.owner_org
            )
        except Exception:
            reply_open = False

        if not reply_open and not (
            current_user
            and (
                current_user.sysadmin
                or has_organization_admin_role(_res.Resource.package.owner_org)
            )
        ):
            helpers.flash_error(
                _('Reply is restricted to administrators.'), allow_html=True
            )
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        if (force_all or not admin_bypass) and is_recaptcha_verified(request) is False:
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        creator_user_id = (
            current_user.id if isinstance(current_user, model.User) else None
        )
        comment_service.create_reply(resource_comment_id, content, creator_user_id)
        session.commit()

        return toolkit.redirect_to('resource_comment.comment', resource_id=resource_id)

    # resource_comment/<resource_id>/comment/<comment_id>/attached_image/<attached_image_filename>
    @staticmethod
    def attached_image(resource_id: str, comment_id: str, attached_image_filename: str):
        resource = comment_service.get_resource(resource_id)
        if resource is None:
            toolkit.abort(404)

        approval = True
        if not isinstance(current_user, model.User):
            # if the user is not logged in, display only approved comments
            approval = True
        elif (
            has_organization_admin_role(resource.Resource.package.owner_org)
            or current_user.sysadmin
        ):
            # if the user is an organization admin or a sysadmin, display all comments
            approval = None

        comment = comment_service.get_resource_comment(
            comment_id, resource_id, approval, attached_image_filename
        )
        if comment is None:
            toolkit.abort(404)
        attached_image_path = comment_service.get_attached_image_path(
            attached_image_filename
        )
        if not os.path.exists(attached_image_path):
            toolkit.abort(404)

        return send_file(attached_image_path)

    @staticmethod
    def _check_organization_admin_role(resource_id):
        resource = comment_service.get_resource(resource_id)
        if (
            not has_organization_admin_role(resource.Resource.package.owner_org)
            and not current_user.sysadmin
        ):
            toolkit.abort(
                404,
                _(
                    'The requested URL was not found on the server. If you entered the'
                    ' URL manually please check your spelling and try again.'
                ),
            )

    def like_status(resource_id):
        status = get_like_status_cookie(resource_id)
        if status:
            return status
        return 'False'

    @staticmethod
    def like_toggle(package_name, resource_id):
        data = request.get_json()
        like_status_raw = data.get('likeStatus')
        like_status_bool = (
            like_status_raw
            if isinstance(like_status_raw, bool)
            else str(like_status_raw).lower() == 'true'
        )

        if like_status_bool:
            likes_service.increment_resource_like_count(resource_id)
            likes_service.increment_resource_like_count_monthly(resource_id)
        else:
            likes_service.decrement_resource_like_count(resource_id)
            likes_service.decrement_resource_like_count_monthly(resource_id)

        session.commit()

        resp = Response("OK", status=200, mimetype='text/plain')
        resp_with_like = set_like_status_cookie(resp, resource_id, like_status_bool)
        return resp_with_like

    # resource_comment/<resource_id>/comment/reactions
    @staticmethod
    @check_administrator
    def reactions(resource_id):
        ResourceController._check_organization_admin_role(resource_id)

        comment_id = request.form.get('resource_comment_id')
        # Normalize and validate comment id
        if comment_id is not None:
            comment_id = comment_id.strip()
        if not comment_id:
            log.error(
                'reactions: missing resource_comment_id (resource_id=%s)', resource_id
            )
            helpers.flash_error(
                _('Failed to change status due to invalid target.'), allow_html=True
            )
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )
        target_comment = comment_service.get_resource_comment(
            comment_id=comment_id, resource_id=resource_id
        )
        if target_comment is None:
            log.error(
                'reactions: comment not found or not belong to resource '
                '(resource_id=%s, comment_id=%s)',
                resource_id,
                comment_id,
            )
            helpers.flash_error(
                _('Failed to change status due to invalid target.'), allow_html=True
            )
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )
        # Use canonical id from DB to avoid empty/invalid ids propagating further
        comment_id = str(getattr(target_comment, 'id'))
        response_status = request.form.get('response_status')
        response_status_map = {
            'status-none': ResourceCommentResponseStatus.STATUS_NONE.name,
            'not-started': ResourceCommentResponseStatus.NOT_STARTED.name,
            'in-progress': ResourceCommentResponseStatus.IN_PROGRESS.name,
            'completed': ResourceCommentResponseStatus.COMPLETED.name,
            'rejected': ResourceCommentResponseStatus.REJECTED.name,
        }
        if response_status not in response_status_map:
            log.error(
                'reactions: invalid response_status=%s '
                '(resource_id=%s, comment_id=%s)',
                response_status,
                resource_id,
                comment_id,
            )
            helpers.flash_error(
                _('Failed to change status due to invalid status value.'),
                allow_html=True,
            )
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )
        mapped_status = response_status_map[response_status]
        admin_liked = request.form.get('admin_liked') == 'on'

        resource_comment_reactions = comment_service.get_resource_comment_reactions(
            comment_id
        )

        if resource_comment_reactions:
            comment_service.update_resource_comment_reactions(
                resource_comment_reactions,
                mapped_status,
                admin_liked,
                current_user.id,
            )
        else:
            comment_service.create_resource_comment_reactions(
                comment_id,
                mapped_status,
                admin_liked,
                current_user.id,
            )

        session.commit()

        return toolkit.redirect_to('resource_comment.comment', resource_id=resource_id)

    @staticmethod
    def _upload_image(image: FileStorage) -> str:
        upload_to = comment_service.get_upload_destination()
        uploader: PUploader = get_uploader(upload_to)
        data_dict = {
            "image_upload": image,
        }
        uploader.update_data_dict(
            data_dict, 'image_url', 'image_upload', 'clear_upload'
        )
        attached_image_filename = data_dict["image_url"]
        uploader.upload()
        return attached_image_filename
