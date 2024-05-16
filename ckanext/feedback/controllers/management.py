from ckan.common import _, current_user, g, request
from ckan.lib import helpers
from ckan.plugins import toolkit
from flask import redirect, url_for

import ckanext.feedback.services.management.comments as comments_service
import ckanext.feedback.services.resource.comment as resource_comment_service
import ckanext.feedback.services.utilization.details as utilization_detail_service
from ckanext.feedback.models.session import session
from ckanext.feedback.services.common.check import (
    check_administrator,
    has_organization_admin_role,
)


class ManagementController:
    # management/comments
    @staticmethod
    @check_administrator
    def comments():
        tab = request.args.get('tab', 'utilization-comments')
        categories = utilization_detail_service.get_utilization_comment_categories()

        # If user is organization admin
        if not current_user.sysadmin:
            ids = current_user.get_group_ids(
                group_type='organization', capacity='admin'
            )
            resource_comments = resource_comment_service.get_resource_comments(
                owner_orgs=ids
            )
            utilization_comments = utilization_detail_service.get_utilization_comments(
                owner_orgs=ids
            )
            g.pkg_dict = {
                'organization': {
                    'name': current_user.get_groups(group_type='organization')[0].name,
                }
            }
        else:
            resource_comments = resource_comment_service.get_resource_comments()
            utilization_comments = utilization_detail_service.get_utilization_comments()
        return toolkit.render(
            'management/comments.html',
            {
                'categories': categories,
                'utilization_comments': utilization_comments,
                'resource_comments': resource_comments,
                'tab': tab,
            },
        )

    # management/approve_bulk_utilization_comments
    @staticmethod
    @check_administrator
    def approve_bulk_utilization_comments():
        comments = request.form.getlist('utilization-comments-checkbox')
        if comments:
            utilizations = comments_service.get_utilizations(comments)
            ManagementController._check_organization_admin_role_with_utilization(
                utilizations
            )
            comments_service.approve_utilization_comments(comments, current_user.id)
            comments_service.refresh_utilizations_comments(utilizations)
            session.commit()
            helpers.flash_success(
                f'{len(comments)} ' + _('bulk approval completed.'),
                allow_html=True,
            )
        return redirect(url_for('management.comments', tab='utilization-comments'))

    # management/approve_bulk_resource_comments
    @staticmethod
    @check_administrator
    def approve_bulk_resource_comments():
        comments = request.form.getlist('resource-comments-checkbox')
        if comments:
            resource_comment_summaries = (
                comments_service.get_resource_comment_summaries(comments)
            )
            ManagementController._check_organization_admin_role_with_resource(
                resource_comment_summaries
            )
            comments_service.approve_resource_comments(comments, current_user.id)
            comments_service.refresh_resources_comments(resource_comment_summaries)
            session.commit()
            helpers.flash_success(
                f'{len(comments)} ' + _('bulk approval completed.'),
                allow_html=True,
            )
        return redirect(url_for('management.comments', tab='resource-comments'))

    # management/delete_bulk_utilization_comments
    @staticmethod
    @check_administrator
    def delete_bulk_utilization_comments():
        comments = request.form.getlist('utilization-comments-checkbox')
        if comments:
            utilizations = comments_service.get_utilizations(comments)
            ManagementController._check_organization_admin_role_with_utilization(
                utilizations
            )
            comments_service.delete_utilization_comments(comments)
            comments_service.refresh_utilizations_comments(utilizations)
            session.commit()

            helpers.flash_success(
                f'{len(comments)} ' + _('bulk delete completed.'),
                allow_html=True,
            )
        return redirect(url_for('management.comments', tab='utilization-comments'))

    # management/delete_bulk_resource_comments
    @staticmethod
    @check_administrator
    def delete_bulk_resource_comments():
        comments = request.form.getlist('resource-comments-checkbox')
        if comments:
            resource_comment_summaries = (
                comments_service.get_resource_comment_summaries(comments)
            )
            ManagementController._check_organization_admin_role_with_resource(
                resource_comment_summaries
            )
            comments_service.delete_resource_comments(comments)
            comments_service.refresh_resources_comments(resource_comment_summaries)
            session.commit()

            helpers.flash_success(
                f'{len(comments)} ' + _('bulk delete completed.'),
                allow_html=True,
            )
        return redirect(url_for('management.comments', tab='resource-comments'))

    @staticmethod
    def _check_organization_admin_role_with_utilization(utilizations):
        for utilization in utilizations:
            if (
                not has_organization_admin_role(utilization.resource.package.owner_org)
                and not current_user.sysadmin
            ):
                toolkit.abort(
                    404,
                    _(
                        'The requested URL was not found on the server. If you entered'
                        ' the URL manually please check your spelling and try again.'
                    ),
                )

    @staticmethod
    def _check_organization_admin_role_with_resource(resource_comment_summaries):
        for resource_comment_summary in resource_comment_summaries:
            if (
                not has_organization_admin_role(
                    resource_comment_summary.resource.package.owner_org
                )
                and not current_user.sysadmin
            ):
                toolkit.abort(
                    404,
                    _(
                        'The requested URL was not found on the server. If you entered'
                        ' the URL manually please check your spelling and try again.'
                    ),
                )
