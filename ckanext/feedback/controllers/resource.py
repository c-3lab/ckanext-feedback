import logging

import ckan.model as model
from ckan.common import _, current_user, g, request
from ckan.lib import helpers
from ckan.logic import get_action
from ckan.plugins import toolkit
from flask import Response, make_response

import ckanext.feedback.services.resource.comment as comment_service
import ckanext.feedback.services.resource.likes as likes_service
import ckanext.feedback.services.resource.summary as summary_service
import ckanext.feedback.services.resource.validate as validate_service
from ckanext.feedback.controllers.pagination import get_pagination_value
from ckanext.feedback.models.resource_comment import ResourceCommentCategory
from ckanext.feedback.models.session import session
from ckanext.feedback.services.common.ai_functions import (
    check_ai_comment,
    suggest_ai_comment,
)
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
    def comment(resource_id, category='', content=''):
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
        cookie = comment_service.get_cookie(resource_id)
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
        if not (category and content):
            toolkit.abort(400)

        if not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return ResourceController.comment(resource_id, category, content)

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return ResourceController.comment(resource_id, category, content)

        if not rating:
            rating = None

        comment_service.create_resource_comment(resource_id, category, content, rating)
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

        resp.set_cookie(resource_id, 'alreadyPosted')

        return resp

    # resource_comment/<resource_id>/comment/suggested
    @staticmethod
    def suggested_comment(resource_id, category='', content='', rating=''):
        softened = suggest_ai_comment(comment=content)

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
        if not (category and content):
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        if not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return ResourceController.comment(resource_id, category, content)

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return ResourceController.comment(resource_id, category, content)

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
            if check_ai_comment(comment=content) is False:
                return ResourceController.suggested_comment(
                    resource_id=resource_id,
                    rating=rating,
                    category=category,
                    content=content,
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
            },
        )

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

    # resource_comment/<resource_id>/comment/reply
    @staticmethod
    @check_administrator
    def reply(resource_id):
        ResourceController._check_organization_admin_role(resource_id)
        resource_comment_id = request.form.get('resource_comment_id', '')
        content = request.form.get('reply_content', '')
        if not (resource_comment_id and content):
            toolkit.abort(400)

        comment_service.create_reply(resource_comment_id, content, current_user.id)
        session.commit()

        return toolkit.redirect_to('resource_comment.comment', resource_id=resource_id)

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
        status = comment_service.get_cookie(resource_id)
        if status:
            return status
        return 'False'

    @staticmethod
    def like_toggle(package_name, resource_id):
        data = request.get_json()
        like_status = data.get('likeStatus')

        if like_status:
            likes_service.increment_resource_like_count(resource_id)
            likes_service.increment_resource_like_count_monthly(resource_id)
        else:
            likes_service.decrement_resource_like_count(resource_id)
            likes_service.decrement_resource_like_count_monthly(resource_id)

        session.commit()

        resp = Response("OK", status=200, mimetype='text/plain')
        resp.set_cookie(resource_id, f'{like_status}', max_age=2147483647)
        return resp
