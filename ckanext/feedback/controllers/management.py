import logging

from ckan.common import _, current_user, g, request
from ckan.lib import helpers
from ckan.plugins import toolkit

import ckanext.feedback.services.management.comments as comments_service
import ckanext.feedback.services.management.feedbacks as feedback_service
import ckanext.feedback.services.management.utilization as utilization_service
import ckanext.feedback.services.resource.comment as resource_comment_service
import ckanext.feedback.services.utilization.details as utilization_detail_service
from ckanext.feedback.controllers.pagination import get_pagination_value
from ckanext.feedback.models.session import session
from ckanext.feedback.services.common.check import (
    check_administrator,
    has_organization_admin_role,
)

log = logging.getLogger(__name__)


class ManagementController:
    # management/feedback-approval
    @staticmethod
    @check_administrator
    def admin():
        active_filters = request.args.getlist('filter')
        sort = request.args.get('sort', 'newest')

        page, limit, offset, pager_url = get_pagination_value(
            'management.feedback-approval'
        )

        # If user is organization admin
        owner_orgs = None
        if not current_user.sysadmin:
            owner_orgs = current_user.get_group_ids(
                group_type='organization', capacity='admin'
            )
            g.pkg_dict = {
                'organization': {
                    'name': current_user.get_groups(group_type='organization')[0].name,
                }
            }
            feedbacks, total_count = feedback_service.get_feedbacks(
                owner_orgs=owner_orgs,
                active_filters=active_filters,
                sort=sort,
                limit=limit,
                offset=offset,
            )
        else:
            feedbacks, total_count = feedback_service.get_feedbacks(
                active_filters=active_filters, sort=sort, limit=limit, offset=offset
            )

        def get_href(name, active_list):
            if name in active_list:
                # 無効化
                active_list.remove(name)
            else:
                # 有効化
                active_list.append(name)

            url = f"{toolkit.url_for('management.feedback-approval')}"
            url_params = request.args
            sort_param = url_params.get('sort')
            if sort_param:
                url += f'?sort={sort_param}'
            for active in active_list:
                url += '?' if '?' not in url else '&'
                url += f'filter={active}'

            return url

        def create_filter_dict(filter_set_name, name_label_dict, active_filters):
            filter_item_list = []
            for name, label in name_label_dict.items():
                filter_item = {}
                filter_item["name"] = name
                filter_item["label"] = label
                filter_item["href"] = get_href(name, active_filters[:])
                filter_item["count"] = feedback_service.get_feedbacks_count(
                    owner_orgs=owner_orgs, active_filters=name
                )
                filter_item["active"] = (
                    False if active_filters == [] else name in active_filters
                )
                filter_item_list.append(filter_item)
            return {"type": filter_set_name, "list": filter_item_list}

        filters = []

        filter_status = {
            "approved": _('Approved'),
            "unapproved": _('Waiting'),
        }

        filter_type = {
            "resource": _('Resource Comment'),
            "utilization": _('Utilization'),
            "util-comment": _('Utilization Comment'),
        }

        filter_org = {}

        if owner_orgs is None:
            org_list = feedback_service.get_org_list()
        else:
            org_list = feedback_service.get_org_list(owner_orgs)

        for org in org_list:
            filter_org[org['name']] = org['title']

        filters.append(create_filter_dict(_('Status'), filter_status, active_filters))
        filters.append(create_filter_dict(_('Type'), filter_type, active_filters))
        filters.append(
            create_filter_dict(_('Organization'), filter_org, active_filters)
        )

        return toolkit.render(
            'management/feedback_status_list.html',
            {
                "filters": filters,
                "sort": sort,
                "page": helpers.Page(
                    collection=feedbacks,
                    page=page,
                    item_count=total_count,
                    items_per_page=limit,
                    url=pager_url,
                ),
            },
        )

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

    # management/approve_bulk_target
    @staticmethod
    @check_administrator
    def approve_bulk_target():
        resource_comments = request.form.getlist('resource-comments-checkbox')
        utilization = request.form.getlist('utilization-checkbox')
        utilization_comments = request.form.getlist('utilization-comments-checkbox')

        if resource_comments:
            ManagementController.approve_bulk_resource_comments(resource_comments)
        if utilization:
            ManagementController.approve_bulk_utilization(utilization)
        if utilization_comments:
            ManagementController.approve_bulk_utilization_comments(utilization_comments)

        return toolkit.redirect_to('management.feedback-approval')

    # management/delete_bulk_target
    @staticmethod
    @check_administrator
    def delete_bulk_target():
        resource_comments = request.form.getlist('resource-comments-checkbox')
        utilization = request.form.getlist('utilization-checkbox')
        utilization_comments = request.form.getlist('utilization-comments-checkbox')

        if resource_comments:
            ManagementController.delete_bulk_resource_comments(resource_comments)
        if utilization:
            ManagementController.delete_bulk_utilization(utilization)
        if utilization_comments:
            ManagementController.delete_bulk_utilization_comments(utilization_comments)

        return toolkit.redirect_to('management.feedback-approval')

    @staticmethod
    @check_administrator
    def approve_bulk_utilization_comments(target):
        target = comments_service.get_utilization_comment_ids(target)
        utilizations = comments_service.get_utilizations(target)
        ManagementController._check_organization_admin_role_with_utilization(
            utilizations
        )
        comments_service.approve_utilization_comments(target, current_user.id)
        comments_service.refresh_utilizations_comments(utilizations)
        session.commit()
        helpers.flash_success(
            f'{len(target)} ' + _('bulk approval completed.'),
            allow_html=True,
        )

    @staticmethod
    @check_administrator
    def approve_bulk_utilization(target):
        target = comments_service.get_utilization_ids(target)
        utilizations = comments_service.get_utilizations(target)
        ManagementController._check_organization_admin_role_with_resource(utilizations)
        utilization_service.approve_utilization(target, current_user.id)
        session.commit()
        helpers.flash_success(
            f'{len(target)} ' + _('bulk approval completed.'),
            allow_html=True,
        )

    @staticmethod
    @check_administrator
    def approve_bulk_resource_comments(target):
        target = comments_service.get_resource_comment_ids(target)
        resource_comment_summaries = comments_service.get_resource_comment_summaries(
            target
        )
        ManagementController._check_organization_admin_role_with_resource(
            resource_comment_summaries
        )
        comments_service.approve_resource_comments(target, current_user.id)
        comments_service.refresh_resources_comments(resource_comment_summaries)
        session.commit()
        helpers.flash_success(
            f'{len(target)} ' + _('bulk approval completed.'),
            allow_html=True,
        )

    @staticmethod
    @check_administrator
    def delete_bulk_utilization_comments(target):
        utilizations = comments_service.get_utilizations(target)
        ManagementController._check_organization_admin_role_with_utilization(
            utilizations
        )
        comments_service.delete_utilization_comments(target)
        comments_service.refresh_utilizations_comments(utilizations)
        session.commit()

        helpers.flash_success(
            f'{len(target)} ' + _('bulk delete completed.'),
            allow_html=True,
        )

    @staticmethod
    @check_administrator
    def delete_bulk_utilization(target):
        utilizations = comments_service.get_utilizations(target)
        ManagementController._check_organization_admin_role_with_utilization(
            utilizations
        )
        utilization_service.delete_utilization(target)
        session.commit()
        helpers.flash_success(
            f'{len(target)} ' + _('bulk delete completed.'),
            allow_html=True,
        )

    @staticmethod
    @check_administrator
    def delete_bulk_resource_comments(target):
        resource_comment_summaries = comments_service.get_resource_comment_summaries(
            target
        )
        ManagementController._check_organization_admin_role_with_resource(
            resource_comment_summaries
        )
        comments_service.delete_resource_comments(target)
        comments_service.refresh_resources_comments(resource_comment_summaries)
        session.commit()

        helpers.flash_success(
            f'{len(target)} ' + _('bulk delete completed.'),
            allow_html=True,
        )

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
