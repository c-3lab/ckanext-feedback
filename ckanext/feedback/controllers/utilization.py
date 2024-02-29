import ckan.model as model
from ckan.common import _, c, request
from ckan.lib import helpers
from ckan.logic import get_action
from ckan.plugins import toolkit
from flask import redirect, url_for

import ckanext.feedback.services.utilization.details as detail_service
import ckanext.feedback.services.utilization.edit as edit_service
import ckanext.feedback.services.utilization.registration as registration_service
import ckanext.feedback.services.utilization.search as search_service
import ckanext.feedback.services.utilization.summary as summary_service
from ckanext.feedback.models.session import session
from ckanext.feedback.services.common.check import (
    check_administrator,
    has_organization_admin_role,
    is_organization_admin,
)


class UtilizationController:
    # Render HTML pages
    # utilization/search
    @staticmethod
    def search():
        id = request.args.get('id', '')
        keyword = request.args.get('keyword', '')
        owner_org = request.args.get('owner_org', '')

        # If the login user is not an admin, display only approved utilizations
        approval = True
        admin_owner_orgs = None
        if c.userobj is None:
            # If the user is not login, display only approved utilizations
            approval = True
        elif c.userobj.sysadmin:
            # If the user is an admin, display all utilizations
            approval = None
        elif is_organization_admin():
            # If the user is an organization admin, display all organization's utilizations
            approval = None
            admin_owner_orgs = c.userobj.get_group_ids(
                group_type='organization', capacity='admin'
            )

        disable_keyword = request.args.get('disable_keyword', '')
        utilizations = search_service.get_utilizations(
            id, keyword, approval, admin_owner_orgs, owner_org
        )

        return toolkit.render(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'utilizations': utilizations,
            },
        )

    # utilization/new
    @staticmethod
    def new():
        resource_id = request.args.get('resource_id', '')
        return_to_resource = request.args.get('return_to_resource', False)
        resource = registration_service.get_resource(resource_id)
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(context, {'id': resource.package.id})

        return toolkit.render(
            'utilization/new.html',
            {
                'pkg_dict': package,
                'return_to_resource': return_to_resource,
                'resource': resource,
            },
        )

    # utilization/new
    @staticmethod
    def create():
        package_name = request.form.get('package_name', '')
        resource_id = request.form.get('resource_id', '')
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        if not (resource_id and title and description):
            toolkit.abort(400)

        return_to_resource = toolkit.asbool(request.form.get('return_to_resource'))
        registration_service.create_utilization(resource_id, title, description)
        summary_service.create_utilization_summary(resource_id)
        session.commit()

        helpers.flash_success(
            _(
                'Your application is complete.<br>The utilization will not be displayed'
                ' until approved by an administrator.'
            ),
            allow_html=True,
        )

        if return_to_resource:
            return redirect(
                url_for('resource.read', id=package_name, resource_id=resource_id)
            )
        else:
            return redirect(url_for('dataset.read', id=package_name))

    # utilization/<utilization_id>
    @staticmethod
    def details(utilization_id):
        approval = True
        utilization = detail_service.get_utilization(utilization_id)
        if c.userobj is None:
            approval = True
        elif has_organization_admin_role(utilization.owner_org) or c.userobj.sysadmin:
            # if the user is an organization admin or a sysadmin, display all comments
            approval = None
        comments = detail_service.get_utilization_comments(utilization_id, approval)
        categories = detail_service.get_utilization_comment_categories()
        issue_resolutions = detail_service.get_issue_resolutions(utilization_id)

        return toolkit.render(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': utilization,
                'comments': comments,
                'categories': categories,
                'issue_resolutions': issue_resolutions,
            },
        )

    # utilization/<utilization_id>/approve
    @staticmethod
    @check_administrator
    def approve(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        resource_id = detail_service.get_utilization(utilization_id).resource_id
        detail_service.approve_utilization(utilization_id, c.userobj.id)
        summary_service.refresh_utilization_summary(resource_id)
        session.commit()

        return redirect(url_for('utilization.details', utilization_id=utilization_id))

    # utilization/<utilization_id>/comment/new
    @staticmethod
    def create_comment(utilization_id):
        category = request.form.get('category', '')
        content = request.form.get('content', '')
        if not (category and content):
            toolkit.abort(400)

        detail_service.create_utilization_comment(utilization_id, category, content)
        session.commit()

        helpers.flash_success(
            _(
                'Your comment has been sent.<br>The comment will not be displayed until'
                ' approved by an administrator.'
            ),
            allow_html=True,
        )

        return redirect(url_for('utilization.details', utilization_id=utilization_id))

    # utilization/<utilization_id>/comment/<comment_id>/approve
    @staticmethod
    @check_administrator
    def approve_comment(utilization_id, comment_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        detail_service.approve_utilization_comment(comment_id, c.userobj.id)
        detail_service.refresh_utilization_comments(utilization_id)
        session.commit()

        return redirect(url_for('utilization.details', utilization_id=utilization_id))

    # utilization/<utilization_id>/edit
    @staticmethod
    @check_administrator
    def edit(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        utilization_details = edit_service.get_utilization_details(utilization_id)
        resource_details = edit_service.get_resource_details(
            utilization_details.resource_id
        )

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
        description = request.form.get('description', '')
        if not (title and description):
            toolkit.abort(400)

        edit_service.update_utilization(utilization_id, title, description)
        session.commit()

        helpers.flash_success(
            _('The utilization has been successfully updated.'),
            allow_html=True,
        )

        return redirect(url_for('utilization.details', utilization_id=utilization_id))

    # utilization/<utilization_id>/delete
    @staticmethod
    @check_administrator
    def delete(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        resource_id = detail_service.get_utilization(utilization_id).resource_id
        edit_service.delete_utilization(utilization_id)
        summary_service.refresh_utilization_summary(resource_id)
        session.commit()

        helpers.flash_success(
            _('The utilization has been successfully deleted.'),
            allow_html=True,
        )

        return redirect(url_for('utilization.search'))

    # utilization/<utilization_id>/issue_resolution/new
    @staticmethod
    @check_administrator
    def create_issue_resolution(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        description = request.form.get('description')
        if not description:
            toolkit.abort(400)

        detail_service.create_issue_resolution(
            utilization_id, description, c.userobj.id
        )
        summary_service.increment_issue_resolution_summary(utilization_id)
        session.commit()

        return redirect(url_for('utilization.details', utilization_id=utilization_id))

    @staticmethod
    def _check_organization_admin_role(utilization_id):
        utilization = detail_service.get_utilization(utilization_id)
        if (
            not has_organization_admin_role(utilization.owner_org)
            and not c.userobj.sysadmin
        ):
            toolkit.abort(
                404,
                _(
                    'The requested URL was not found on the server. If you entered the'
                    ' URL manually please check your spelling and try again.'
                ),
            )
