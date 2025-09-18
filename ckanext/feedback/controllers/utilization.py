import logging
import os

import ckan.model as model
from ckan.common import _, current_user, g, request
from ckan.lib import helpers
from ckan.lib.uploader import get_uploader
from ckan.logic import get_action
from ckan.plugins import toolkit
from ckan.types import PUploader
from flask import send_file
from werkzeug.datastructures import FileStorage

import ckanext.feedback.services.resource.comment as comment_service
import ckanext.feedback.services.utilization.details as detail_service
import ckanext.feedback.services.utilization.edit as edit_service
import ckanext.feedback.services.utilization.registration as registration_service
import ckanext.feedback.services.utilization.search as search_service
import ckanext.feedback.services.utilization.summary as summary_service
import ckanext.feedback.services.utilization.validate as validate_service
from ckanext.feedback.controllers.pagination import get_pagination_value
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import UtilizationCommentCategory
from ckanext.feedback.services.common.ai_functions import (
    check_ai_comment,
    suggest_ai_comment,
)
from ckanext.feedback.services.common.check import (
    check_administrator,
    has_organization_admin_role,
    is_organization_admin,
)
from ckanext.feedback.services.common.config import FeedbackConfig
from ckanext.feedback.services.common.send_mail import send_email
from ckanext.feedback.services.recaptcha.check import is_recaptcha_verified

log = logging.getLogger(__name__)


class UtilizationController:
    # Render HTML pages
    # utilization/search
    @staticmethod
    def search():
        id = request.args.get('id', '')
        keyword = request.args.get('keyword', '')
        org_name = request.args.get('organization', '')

        unapproved_status = request.args.get('waiting', 'on')
        approval_status = request.args.get('approval', 'on')

        page, limit, offset, pager_url = get_pagination_value('utilization.search')

        # If the login user is not an admin, display only approved utilizations
        approval = True
        admin_owner_orgs = None
        if not isinstance(current_user, model.User):
            # If the user is not login, display only approved utilizations
            approval = True
        elif current_user.sysadmin:
            # If the user is an admin, display all utilizations
            approval = None
        elif is_organization_admin():
            # If the user is an organization admin, display all utilizations
            approval = None
            admin_owner_orgs = current_user.get_group_ids(
                group_type='organization', capacity='admin'
            )

        disable_keyword = request.args.get('disable_keyword', '')
        utilizations, total_count = search_service.get_utilizations(
            id,
            keyword,
            approval,
            admin_owner_orgs,
            org_name,
            limit,
            offset,
        )

        # If the organization name can be identified,
        # set it as a global variable accessible from templates.
        if id and not org_name:
            resource = comment_service.get_resource(id)
            if resource:
                org_name = resource.organization_name
            else:
                org_name = search_service.get_organization_name_from_pkg(id)
        if org_name:
            g.pkg_dict = {
                'organization': {
                    'name': org_name,
                },
            }

        return toolkit.render(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'unapproved_status': unapproved_status,
                'approval_status': approval_status,
                'page': helpers.Page(
                    collection=utilizations,
                    page=page,
                    url=pager_url,
                    item_count=total_count,
                    items_per_page=limit,
                ),
            },
        )

    # utilization/new
    @staticmethod
    def new(resource_id=None, title='', description=''):
        if not resource_id:
            resource_id = request.args.get('resource_id', '')
        return_to_resource = request.args.get('return_to_resource', False)
        resource = comment_service.get_resource(resource_id)
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': resource.Resource.package.id}
        )
        g.pkg_dict = {'organization': {'name': resource.organization_name}}

        return toolkit.render(
            'utilization/new.html',
            {
                'pkg_dict': package,
                'return_to_resource': return_to_resource,
                'resource': resource.Resource,
            },
        )

    # utilization/new
    @staticmethod
    def create():
        package_name = request.form.get('package_name', '')
        resource_id = request.form.get('resource_id', '')
        title = request.form.get('title', '')
        url = request.form.get('url', '')
        description = request.form.get('description', '')

        url_err_msg = validate_service.validate_url(url)
        title_err_msg = validate_service.validate_title(title)
        dsc_err_msg = validate_service.validate_description(description)
        if (url and url_err_msg) or title_err_msg or dsc_err_msg:
            if title_err_msg:
                helpers.flash_error(
                    _(title_err_msg),
                    allow_html=True,
                )
            if url and url_err_msg:
                helpers.flash_error(
                    _(url_err_msg),
                    allow_html=True,
                )
            if dsc_err_msg:
                helpers.flash_error(
                    _(dsc_err_msg),
                    allow_html=True,
                )
            return toolkit.redirect_to(
                'utilization.new',
                resource_id=resource_id,
            )

        if not (resource_id and title and description):
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
        if (force_all or not admin_bypass) and not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return toolkit.redirect_to(
                'utilization.new',
                resource_id=resource_id,
                title=title,
                description=description,
            )
        return_to_resource = toolkit.asbool(request.form.get('return_to_resource'))
        utilization = registration_service.create_utilization(
            resource_id, title, url, description
        )
        summary_service.create_utilization_summary(resource_id)
        utilization_id = utilization.id
        session.commit()

        try:
            resource = comment_service.get_resource(resource_id)
            send_email(
                template_name=FeedbackConfig().notice_email.template_utilization.get(),
                organization_id=resource.Resource.package.owner_org,
                subject=FeedbackConfig().notice_email.subject_utilization.get(),
                target_name=resource.Resource.name,
                content_title=title,
                content=description,
                url=toolkit.url_for(
                    'utilization.details', utilization_id=utilization_id, _external=True
                ),
            )
        except Exception:
            log.exception('Send email failed, for feedback notification.')

        helpers.flash_success(
            _(
                'Your application is complete.<br>The utilization will not be displayed'
                ' until approved by an administrator.'
            ),
            allow_html=True,
        )

        if return_to_resource:
            return toolkit.redirect_to(
                'resource.read', id=package_name, resource_id=resource_id
            )
        else:
            return toolkit.redirect_to('dataset.read', id=package_name)

    # utilization/<utilization_id>
    @staticmethod
    def details(
        utilization_id,
        category='',
        content='',
        attached_image_filename: str | None = None,
    ):
        approval = True
        utilization = detail_service.get_utilization(utilization_id)
        if not isinstance(current_user, model.User):
            approval = True
        elif (
            has_organization_admin_role(utilization.owner_org) or current_user.sysadmin
        ):
            # if the user is an organization admin or a sysadmin, display all comments
            approval = None

        page, limit, offset, _ = get_pagination_value('utilization.details')

        comments, total_count = detail_service.get_utilization_comments(
            utilization_id, approval, limit=limit, offset=offset
        )

        categories = detail_service.get_utilization_comment_categories()
        issue_resolutions = detail_service.get_issue_resolutions(utilization_id)
        g.pkg_dict = {
            'organization': {
                'name': (
                    comment_service.get_resource(
                        utilization.resource_id
                    ).organization_name
                )
            }
        }
        if not category:
            selected_category = UtilizationCommentCategory.REQUEST.name
        else:
            selected_category = category

        return toolkit.render(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': utilization,
                'categories': categories,
                'issue_resolutions': issue_resolutions,
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

    # utilization/<utilization_id>/approve
    @staticmethod
    @check_administrator
    def approve(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        resource_id = detail_service.get_utilization(utilization_id).resource_id
        detail_service.approve_utilization(utilization_id, current_user.id)
        summary_service.refresh_utilization_summary(resource_id)
        session.commit()

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/new
    @staticmethod
    def create_comment(utilization_id):
        category = request.form.get('category', '')
        content = request.form.get('comment-content', '')
        attached_image_filename = request.form.get('attached_image_filename', None)
        if not (category and content):
            toolkit.abort(400)

        attached_image: FileStorage = request.files.get("image-upload")
        if attached_image:
            try:
                attached_image_filename = UtilizationController._upload_image(
                    attached_image
                )
            except toolkit.ValidationError as e:
                helpers.flash_error(e.error_summary, allow_html=True)
                return UtilizationController.details(utilization_id, category, content)
            except Exception as e:
                log.exception(f'Exception: {e}')
                toolkit.abort(500)

        # Admins (org-admin or sysadmin) skip reCAPTCHA unless forced
        force_all = toolkit.asbool(FeedbackConfig().recaptcha.force_all.get())
        admin_bypass = False
        if isinstance(current_user, model.User):
            try:
                _uti = detail_service.get_utilization(utilization_id)
                admin_bypass = current_user.sysadmin or has_organization_admin_role(
                    _uti.owner_org
                )
            except Exception:
                admin_bypass = current_user.sysadmin
        if (force_all or not admin_bypass) and not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return UtilizationController.details(
                utilization_id, category, content, attached_image_filename
            )

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return toolkit.redirect_to(
                'utilization.details',
                utilization_id=utilization_id,
                category=category,
                attached_image_filename=attached_image_filename,
            )

        detail_service.create_utilization_comment(
            utilization_id, category, content, attached_image_filename
        )

        session.commit()

        category_map = {
            UtilizationCommentCategory.REQUEST.name: _('Request'),
            UtilizationCommentCategory.QUESTION.name: _('Question'),
            UtilizationCommentCategory.THANK.name: _('Thank'),
        }

        try:
            utilization = detail_service.get_utilization(utilization_id)
            send_email(
                template_name=(
                    FeedbackConfig().notice_email.template_utilization_comment.get()
                ),
                organization_id=comment_service.get_resource(
                    utilization.resource_id
                ).Resource.package.owner_org,
                subject=FeedbackConfig().notice_email.subject_utilization_comment.get(),
                target_name=utilization.title,
                category=category_map[category],
                content=content,
                url=toolkit.url_for(
                    'utilization.details', utilization_id=utilization_id, _external=True
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

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/reply
    @staticmethod
    def reply(utilization_id):
        utilization_comment_id = request.form.get('utilization_comment_id', '')
        content = request.form.get('reply_content', '')
        if not (utilization_comment_id and content):
            toolkit.abort(400)

        # Get utilization first to avoid UnboundLocalError
        try:
            _uti = detail_service.get_utilization(utilization_id)
        except Exception:
            helpers.flash_error(_('Utilization not found.'), allow_html=True)
            return toolkit.redirect_to('utilization.search')

        # Admins (org-admin or sysadmin) skip reCAPTCHA unless forced
        force_all = toolkit.asbool(FeedbackConfig().recaptcha.force_all.get())
        admin_bypass = False
        if isinstance(current_user, model.User):
            try:
                admin_bypass = current_user.sysadmin or has_organization_admin_role(
                    _uti.owner_org
                )
            except Exception:
                admin_bypass = current_user.sysadmin

        # Reply permission control (admin or reply_open)
        reply_open = False
        try:
            reply_open = FeedbackConfig().utilization_comment.reply_open.is_enable(
                _uti.owner_org
            )
        except Exception:
            reply_open = False
        is_org_admin = False
        try:
            is_org_admin = has_organization_admin_role(_uti.owner_org)
        except Exception:
            is_org_admin = False
        if not reply_open and not (
            is_org_admin
            or (isinstance(current_user, model.User) and current_user.sysadmin)
        ):
            helpers.flash_error(
                _('Reply is restricted to administrators.'), allow_html=True
            )
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        if (force_all or not admin_bypass) and is_recaptcha_verified(request) is False:
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        creator_user_id = (
            current_user.id if isinstance(current_user, model.User) else None
        )
        attached_image_filename = None
        attached_image: FileStorage = request.files.get("attached_image")
        if attached_image:
            try:
                attached_image_filename = UtilizationController._upload_image(
                    attached_image
                )
            except toolkit.ValidationError as e:
                helpers.flash_error(e.error_summary, allow_html=True)
                return toolkit.redirect_to(
                    'utilization.details', utilization_id=utilization_id
                )
            except Exception as e:
                log.exception(f'Exception: {e}')
                toolkit.abort(500)

        detail_service.create_utilization_comment_reply(
            utilization_comment_id, content, creator_user_id, attached_image_filename
        )
        session.commit()

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/reply/attached_image/<reply_id>/<attached_image_filename>
    @staticmethod
    def reply_attached_image(
        utilization_id: str, reply_id: str, attached_image_filename: str
    ):
        utilization = detail_service.get_utilization(utilization_id)
        if utilization is None:
            toolkit.abort(404)

        approval = True
        if isinstance(current_user, model.User) and (
            current_user.sysadmin or has_organization_admin_role(utilization.owner_org)
        ):
            approval = None

        from ckanext.feedback.models.session import session as _session
        from ckanext.feedback.models.utilization import (
            UtilizationComment,
            UtilizationCommentReply,
        )

        q = (
            _session.query(UtilizationCommentReply)
            .join(
                UtilizationComment,
                UtilizationCommentReply.utilization_comment_id == UtilizationComment.id,
            )
            .filter(
                UtilizationCommentReply.id == reply_id,
                UtilizationComment.utilization_id == utilization_id,
            )
        )
        if approval is not None:
            q = q.filter(UtilizationCommentReply.approval == approval)
        reply = q.first()
        if reply is None or reply.attached_image_filename != attached_image_filename:
            toolkit.abort(404)

        attached_image_path = detail_service.get_attached_image_path(
            attached_image_filename
        )
        if not os.path.exists(attached_image_path):
            toolkit.abort(404)
        return send_file(attached_image_path)

    # utilization/<utilization_id>/comment/suggested
    @staticmethod
    def suggested_comment(
        utilization_id,
        category,
        content,
        attached_image_filename: str | None = None,
    ):
        softened = suggest_ai_comment(comment=content)

        utilization = detail_service.get_utilization(utilization_id)
        g.pkg_dict = {
            'organization': {
                'name': (
                    comment_service.get_resource(
                        utilization.resource_id
                    ).organization_name
                )
            }
        }

        if softened is None:
            return toolkit.render(
                'utilization/expect_suggestion.html',
                {
                    'utilization_id': utilization_id,
                    'utilization': utilization,
                    'selected_category': category,
                    'content': content,
                    'attached_image_filename': attached_image_filename,
                },
            )

        return toolkit.render(
            'utilization/suggestion.html',
            {
                'utilization_id': utilization_id,
                'utilization': utilization,
                'selected_category': category,
                'content': content,
                'attached_image_filename': attached_image_filename,
                'softened': softened,
            },
        )

    # utilization/<utilization_id>/comment/check
    @staticmethod
    def check_comment(utilization_id):
        if request.method == 'GET':
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        category = request.form.get('category', '')
        content = request.form.get('comment-content', '')
        attached_image_filename = request.form.get('attached_image_filename', None)
        if not (category and content):
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        attached_image: FileStorage = request.files.get("attached_image")
        if attached_image:
            try:
                attached_image_filename = UtilizationController._upload_image(
                    attached_image
                )
            except toolkit.ValidationError as e:
                helpers.flash_error(e.error_summary, allow_html=True)
                return UtilizationController.details(utilization_id, category, content)
            except Exception as e:
                log.exception(f'Exception: {e}')
                toolkit.abort(500)

        # Admins (org-admin or sysadmin) skip reCAPTCHA unless forced
        force_all = toolkit.asbool(FeedbackConfig().recaptcha.force_all.get())
        admin_bypass = False
        if isinstance(current_user, model.User):
            try:
                _uti = detail_service.get_utilization(utilization_id)
                admin_bypass = current_user.sysadmin or has_organization_admin_role(
                    _uti.owner_org
                )
            except Exception:
                admin_bypass = current_user.sysadmin
        if (force_all or not admin_bypass) and not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return UtilizationController.details(
                utilization_id, category, content, attached_image_filename
            )

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return toolkit.redirect_to(
                'utilization.details',
                utilization_id=utilization_id,
                category=category,
                attached_image_filename=attached_image_filename,
            )

        categories = detail_service.get_utilization_comment_categories()
        utilization = detail_service.get_utilization(utilization_id)
        resource = comment_service.get_resource(utilization.resource_id)
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
            if check_ai_comment(comment=content) is False:
                return UtilizationController.suggested_comment(
                    utilization_id=utilization_id,
                    category=category,
                    content=content,
                    attached_image_filename=attached_image_filename,
                )

        return toolkit.render(
            'utilization/comment_check.html',
            {
                'pkg_dict': package,
                'utilization_id': utilization_id,
                'utilization': utilization,
                'content': content,
                'selected_category': category,
                'categories': categories,
                'attached_image_filename': attached_image_filename,
            },
        )

    # <utilization_id>/comment/check/attached_image/<attached_image_filename>
    @staticmethod
    def check_attached_image(utilization_id: str, attached_image_filename: str):
        attached_image_path = detail_service.get_attached_image_path(
            attached_image_filename
        )
        return send_file(attached_image_path)

    # utilization/<utilization_id>/comment/<comment_id>/approve
    @staticmethod
    @check_administrator
    def approve_comment(utilization_id, comment_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        detail_service.approve_utilization_comment(comment_id, current_user.id)
        detail_service.refresh_utilization_comments(utilization_id)
        session.commit()

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/reply/<reply_id>/approve
    @staticmethod
    @check_administrator
    def approve_reply(utilization_id, reply_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        try:
            detail_service.approve_utilization_comment_reply(reply_id, current_user.id)
            session.commit()
        except ValueError as e:
            log.warning(f'approve_reply ValueError: {e}')
        except PermissionError:
            helpers.flash_error(
                _('Cannot approve reply because its parent comment is not approved.'),
                allow_html=True,
            )
        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/edit
    @staticmethod
    @check_administrator
    def edit(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        utilization_details = edit_service.get_utilization_details(utilization_id)
        resource_details = edit_service.get_resource_details(
            utilization_details.resource_id
        )
        g.pkg_dict = {
            'organization': {
                'name': (
                    comment_service.get_resource(
                        utilization_details.resource_id
                    ).organization_name
                )
            }
        }

        return toolkit.render(
            'utilization/edit.html',
            {
                'utilization_details': utilization_details,
                'resource_details': resource_details,
            },
        )

    # utilization/<utilization_id>/edit
    @staticmethod
    @check_administrator
    def update(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        title = request.form.get('title', '')
        url = request.form.get('url', '')
        description = request.form.get('description', '')
        if not (title and description):
            toolkit.abort(400)

        url_err_msg = validate_service.validate_url(url)
        title_err_msg = validate_service.validate_title(title)
        dsc_err_msg = validate_service.validate_description(description)
        if (url and url_err_msg) or title_err_msg or dsc_err_msg:
            if title_err_msg:
                helpers.flash_error(
                    _(title_err_msg),
                    allow_html=True,
                )
            if url and url_err_msg:
                helpers.flash_error(
                    _(url_err_msg),
                    allow_html=True,
                )
            if dsc_err_msg:
                helpers.flash_error(
                    _(dsc_err_msg),
                    allow_html=True,
                )
            return toolkit.redirect_to(
                'utilization.edit',
                utilization_id=utilization_id,
            )

        edit_service.update_utilization(utilization_id, title, url, description)
        session.commit()

        helpers.flash_success(
            _('The utilization has been successfully updated.'),
            allow_html=True,
        )

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/delete
    @staticmethod
    @check_administrator
    def delete(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        resource_id = detail_service.get_utilization(utilization_id).resource_id
        edit_service.delete_utilization(utilization_id)
        session.commit()
        summary_service.refresh_utilization_summary(resource_id)
        session.commit()

        helpers.flash_success(
            _('The utilization has been successfully deleted.'),
            allow_html=True,
        )

        return toolkit.redirect_to('utilization.search')

    # utilization/<utilization_id>/issue_resolution/new
    @staticmethod
    @check_administrator
    def create_issue_resolution(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        description = request.form.get('description')
        if not description:
            toolkit.abort(400)

        detail_service.create_issue_resolution(
            utilization_id, description, current_user.id
        )
        summary_service.increment_issue_resolution_summary(utilization_id)
        session.commit()

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/<comment_id>/attached_image/<attached_image_filename>
    @staticmethod
    def attached_image(
        utilization_id: str, comment_id: str, attached_image_filename: str
    ):
        utilization = detail_service.get_utilization(utilization_id)
        if utilization is None:
            toolkit.abort(404)

        approval = True
        if not isinstance(current_user, model.User):
            # if the user is not logged in, display only approved comments
            approval = True
        elif (
            has_organization_admin_role(utilization.owner_org) or current_user.sysadmin
        ):
            # if the user is an organization admin or a sysadmin, display all comments
            approval = None

        comment = detail_service.get_utilization_comment(
            comment_id, utilization_id, approval, attached_image_filename
        )
        if comment is None:
            toolkit.abort(404)
        attached_image_path = detail_service.get_attached_image_path(
            attached_image_filename
        )
        if not os.path.exists(attached_image_path):
            toolkit.abort(404)

        return send_file(attached_image_path)

    @staticmethod
    def _check_organization_admin_role(utilization_id):
        utilization = detail_service.get_utilization(utilization_id)
        if (
            not has_organization_admin_role(utilization.owner_org)
            and not current_user.sysadmin
        ):
            toolkit.abort(
                404,
                _(
                    'The requested URL was not found on the server. If you entered the'
                    ' URL manually please check your spelling and try again.'
                ),
            )

    @staticmethod
    def _upload_image(image: FileStorage) -> str:
        upload_to = detail_service.get_upload_destination()
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
