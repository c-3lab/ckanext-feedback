import logging

from ckan.common import _, current_user, g, request
from ckan.lib import helpers
from ckan.plugins import toolkit

from ckanext.feedback.controllers.pagination import get_pagination_value
from ckanext.feedback.models.session import session
from ckanext.feedback.services.admin import feedbacks as feedback_service
from ckanext.feedback.services.admin import (
    resource_comments as resource_comments_service,
)
from ckanext.feedback.services.admin import utilization as utilization_service
from ckanext.feedback.services.admin import (
    utilization_comments as utilization_comments_service,
)
from ckanext.feedback.services.common.check import (
    check_administrator,
    has_organization_admin_role,
)
from ckanext.feedback.services.organization import organization as organization_service

log = logging.getLogger(__name__)


class ManagementController:
    # management/top
    @staticmethod
    @check_administrator
    def management():
        management_list = [
            {
                'name': _('Approval and Delete'),
                'url': 'feedback.approval-delete',
                'description': _(
                    'You can change the approval status of resource comments '
                    'to the organization, utilization requests, '
                    'or comments on registered utilizations.'
                ),
            },
        ]

        return toolkit.render(
            'admin/management.html',
            {'management_list': management_list},
        )

    def get_href(name, active_list):
        if name in active_list:
            # 無効化
            active_list.remove(name)
        else:
            # 有効化
            active_list.append(name)

        url = f"{toolkit.url_for('feedback.approval-delete')}"

        sort_param = request.args.get('sort')
        if sort_param:
            url += f'?sort={sort_param}'

        for active in active_list:
            url += '?' if '?' not in url else '&'
            url += f'filter={active}'

        return url

    def create_filter_dict(
        filter_set_name, name_label_dict, active_filters, owner_orgs
    ):
        filter_item_list = []
        for name, label in name_label_dict.items():
            filter_item = {}
            filter_item["name"] = name
            filter_item["label"] = label
            filter_item["href"] = ManagementController.get_href(name, active_filters[:])
            filter_item["count"] = feedback_service.get_feedbacks_count(
                owner_orgs=owner_orgs, active_filters=name
            )
            filter_item["active"] = (
                False if active_filters == [] else name in active_filters
            )
            filter_item_list.append(filter_item)
        return {"type": filter_set_name, "list": filter_item_list}

    # management/feedback-approval
    @staticmethod
    @check_administrator
    def admin():
        active_filters = request.args.getlist('filter')
        sort = request.args.get('sort', 'newest')

        page, limit, offset, pager_url = get_pagination_value(
            'feedback.approval-delete'
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
            org_list = organization_service.get_org_list()
        else:
            org_list = organization_service.get_org_list(owner_orgs)

        for org in org_list:
            filter_org[org['name']] = org['title']

        filters.append(
            ManagementController.create_filter_dict(
                _('Status'), filter_status, active_filters, owner_orgs
            )
        )
        filters.append(
            ManagementController.create_filter_dict(
                _('Type'), filter_type, active_filters, owner_orgs
            )
        )
        filters.append(
            ManagementController.create_filter_dict(
                _('Organization'), filter_org, active_filters, owner_orgs
            )
        )

        return toolkit.render(
            'admin/approval_delete.html',
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

    # feedback/management/approve_target
    @staticmethod
    @check_administrator
    def approve_target():
        resource_comments = request.form.getlist('resource-comments-checkbox')
        utilization = request.form.getlist('utilization-checkbox')
        utilization_comments = request.form.getlist('utilization-comments-checkbox')

        target = 0

        if resource_comments:
            target += ManagementController.approve_resource_comments(resource_comments)
        if utilization:
            target += ManagementController.approve_utilization(utilization)
        if utilization_comments:
            target += ManagementController.approve_utilization_comments(
                utilization_comments
            )

        helpers.flash_success(
            f'{target} ' + _('approval completed.'),
            allow_html=True,
        )

        return toolkit.redirect_to('feedback.approval-delete')

    # feedback/management/delete_target
    @staticmethod
    @check_administrator
    def delete_target():
        resource_comments = request.form.getlist('resource-comments-checkbox')
        utilization = request.form.getlist('utilization-checkbox')
        utilization_comments = request.form.getlist('utilization-comments-checkbox')

        target = 0

        if resource_comments:
            target += ManagementController.delete_resource_comments(resource_comments)
        if utilization:
            target += ManagementController.delete_utilization(utilization)
        if utilization_comments:
            target += ManagementController.delete_utilization_comments(
                utilization_comments
            )

        helpers.flash_success(
            f'{target} ' + _('delete completed.'),
            allow_html=True,
        )

        return toolkit.redirect_to('feedback.approval-delete')

    @staticmethod
    @check_administrator
    def approve_utilization_comments(target):
        target = utilization_comments_service.get_utilization_comment_ids(target)
        utilizations = utilization_service.get_utilizations(target)
        ManagementController._check_organization_admin_role_with_utilization(
            utilizations
        )
        utilization_comments_service.approve_utilization_comments(
            target, current_user.id
        )
        utilization_comments_service.refresh_utilizations_comments(utilizations)
        session.commit()

        return len(target)

    @staticmethod
    @check_administrator
    def approve_utilization(target):
        target = utilization_service.get_utilization_ids(target)
        utilizations = utilization_service.get_utilizations(target)
        ManagementController._check_organization_admin_role_with_resource(utilizations)
        utilization_service.approve_utilization(target, current_user.id)
        session.commit()

        return len(target)

    @staticmethod
    @check_administrator
    def approve_resource_comments(target):
        target = resource_comments_service.get_resource_comment_ids(target)
        resource_comment_summaries = (
            resource_comments_service.get_resource_comment_summaries(target)
        )
        ManagementController._check_organization_admin_role_with_resource(
            resource_comment_summaries
        )
        resource_comments_service.approve_resource_comments(target, current_user.id)
        resource_comments_service.refresh_resources_comments(resource_comment_summaries)
        session.commit()

        return len(target)

    @staticmethod
    @check_administrator
    def delete_utilization_comments(target):
        utilizations = utilization_service.get_utilizations(target)
        ManagementController._check_organization_admin_role_with_utilization(
            utilizations
        )
        utilization_comments_service.delete_utilization_comments(target)
        utilization_comments_service.refresh_utilizations_comments(utilizations)
        session.commit()

        return len(target)

    @staticmethod
    @check_administrator
    def delete_utilization(target):
        utilizations = utilization_service.get_utilizations(target)
        ManagementController._check_organization_admin_role_with_utilization(
            utilizations
        )
        utilization_service.delete_utilization(target)
        session.commit()

        return len(target)

    @staticmethod
    @check_administrator
    def delete_resource_comments(target):
        resource_comment_summaries = (
            resource_comments_service.get_resource_comment_summaries(target)
        )
        ManagementController._check_organization_admin_role_with_resource(
            resource_comment_summaries
        )
        resource_comments_service.delete_resource_comments(target)
        resource_comments_service.refresh_resources_comments(resource_comment_summaries)
        session.commit()

        return len(target)

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
