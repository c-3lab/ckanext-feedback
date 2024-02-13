import ckan.model as model
from ckan.common import _, c, request
from ckan.lib import helpers
from ckan.logic import get_action
from ckan.plugins import toolkit
from flask import make_response, redirect, url_for

import ckanext.feedback.services.resource.comment as comment_service
import ckanext.feedback.services.resource.summary as summary_service
from ckanext.feedback.models.session import session
from ckanext.feedback.services.common.check import check_administrator, has_organization_admin_role


class ResourceController:
    # Render HTML pages
    # resource_comment/<resource_id>
    @staticmethod
    def comment(resource_id):
        approval = None
        resource = comment_service.get_resource(resource_id)
        # If the user is not login or is not a sysadmin, display only approved comments
        if c.userobj is None or not c.userobj.sysadmin:
            approval = True

        # If the user is an organization admin, display all comments
        if c.userobj is not None:
            owner_org = resource.package.owner_org
            ids = c.userobj.get_group_ids(group_type='organization', capacity='admin')
            if owner_org in ids:
                approval = None
        comments = comment_service.get_resource_comments(resource_id, approval)
        categories = comment_service.get_resource_comment_categories()
        cookie = comment_service.get_cookie(resource_id)
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(context, {'id': resource.package_id})

        return toolkit.render(
            'resource/comment.html',
            {
                'resource': resource,
                'pkg_dict': package,
                'comments': comments,
                'categories': categories,
                'cookie': cookie,
            },
        )

    # resource_comment/<resource_id>/comment/new
    @staticmethod
    def create_comment(resource_id):
        category = None
        content = None
        if request.form.get('comment_content'):
            content = request.form.get('comment_content')
            category = request.form.get('category')
        rating = None
        if request.form.get('rating'):
            rating = int(request.form.get('rating'))
        if not ((category and content) or rating):
            toolkit.abort(400)

        comment_service.create_resource_comment(resource_id, category, content, rating)
        summary_service.create_resource_summary(resource_id)
        session.commit()

        helpers.flash_success(
            _(
                'Your comment has been sent.<br>The comment will not be displayed until'
                ' approved by an administrator.'
            ),
            allow_html=True,
        )

        resp = make_response(
            redirect(url_for('resource_comment.comment', resource_id=resource_id))
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

        comment_service.approve_resource_comment(resource_comment_id, c.userobj.id)
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

        comment_service.create_reply(resource_comment_id, content, c.userobj.id)
        session.commit()

        return redirect(url_for('resource_comment.comment', resource_id=resource_id))

    @staticmethod
    def _check_organization_admin_role(resource_id):
        resource = comment_service.get_resource(resource_id)
        if not has_organization_admin_role(resource.package.owner_org):
            toolkit.abort(
                404,
                _(
                    'The requested URL was not found on the server. If you entered the'
                    ' URL manually please check your spelling and try again.'
                ),
            )
