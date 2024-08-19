import logging

import ckan.model as model
from ckan.common import _, config, current_user, g, request
from ckan.lib import helpers
from ckan.logic import get_action
from ckan.plugins import toolkit
from flask import make_response, redirect, url_for

import ckanext.feedback.services.resource.comment as comment_service
import ckanext.feedback.services.resource.summary as summary_service
import ckanext.feedback.services.resource.validate as validate_service
from ckanext.feedback.models.session import session
from ckanext.feedback.services.common.check import (
    check_administrator,
    has_organization_admin_role,
)
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

        comments = comment_service.get_resource_comments(resource_id, approval)
        categories = comment_service.get_resource_comment_categories()
        cookie = comment_service.get_cookie(resource_id)
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': resource.Resource.package_id}
        )
        g.pkg_dict = {'organization': {'name': resource.organization_name}}

        return toolkit.render(
            'resource/comment.html',
            {
                'resource': resource.Resource,
                'pkg_dict': package,
                'comments': comments,
                'categories': categories,
                'cookie': cookie,
                'selected_category': category,
                'content': content,
            },
        )

    # resource_comment/<resource_id>/comment/new
    @staticmethod
    def create_comment(resource_id):
        package_name = request.form.get('package_name', '')
        category = None
        content = None
        if request.form.get('comment-content'):
            content = request.form.get('comment-content')
            category = request.form.get('category')
        rating = None
        if request.form.get('rating'):
            rating = int(request.form.get('rating'))
        if not (category and content):
            toolkit.abort(400)

        if not is_recaptcha_verified(request):
            helpers.flash_error(_(u'Bad Captcha. Please try again.'), allow_html=True)
            return ResourceController.comment(resource_id, category, content)

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return ResourceController.comment(resource_id, category, content)

        comment_service.create_resource_comment(resource_id, category, content, rating)
        summary_service.create_resource_summary(resource_id)
        session.commit()

        try:
            resource = comment_service.get_resource(resource_id)
            send_email(
                template_name=config.get(
                    'ckan.feedback.notice.email.template_resource_comment'
                ),
                organization_id=resource.Resource.package.owner_org,
                subject=config.get(
                    'ckan.feedback.notice.email.subject_resource_comment'
                ),
                target_name=resource.Resource.name,
                category=category,
                content=content,
                url=url_for(
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
            redirect(url_for('resource.read', id=package_name, resource_id=resource_id))
        )

        resp.set_cookie(resource_id, 'alreadyPosted')

        return resp

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

        return redirect(url_for('resource_comment.comment', resource_id=resource_id))

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

        return redirect(url_for('resource_comment.comment', resource_id=resource_id))

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
