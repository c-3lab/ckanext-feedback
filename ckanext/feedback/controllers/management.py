from ckan.common import _, c, request
from ckan.lib import helpers
from ckan.plugins import toolkit
from flask import redirect, url_for

import ckanext.feedback.services.management.comments as comments_service
import ckanext.feedback.services.resource.comment as resource_comment_service
import ckanext.feedback.services.utilization.details as utilization_detail_service
from ckanext.feedback.models.session import session
from ckanext.feedback.services.common.check import check_administrator


class ManagementController:
    # management/comments
    @staticmethod
    @check_administrator
    def comments():
        tab = request.args.get('tab', 'utilization-comments')
        categories = utilization_detail_service.get_utilization_comment_categories()
        utilization_comments = utilization_detail_service.get_utilization_comments()
        # User is organization admin
        if not c.userobj.sysadmin:
            ids = c.userobj.get_group_ids(group_type='organization', capacity='admin')
            resource_comments = resource_comment_service.get_resource_comments(owner_orgs=ids)
        else:
            resource_comments = resource_comment_service.get_resource_comments()
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
            comments_service.approve_utilization_comments(comments, c.userobj.id)
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
            comments_service.approve_resource_comments(comments, c.userobj.id)
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
            comments_service.delete_resource_comments(comments)
            comments_service.refresh_resources_comments(resource_comment_summaries)
            session.commit()

            helpers.flash_success(
                f'{len(comments)} ' + _('bulk delete completed.'),
                allow_html=True,
            )
        return redirect(url_for('management.comments', tab='resource-comments'))
