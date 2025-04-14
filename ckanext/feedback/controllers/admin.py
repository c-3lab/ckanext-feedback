import csv
import io
import logging
import urllib.parse
from datetime import datetime

from ckan.common import _, current_user, g, request
from ckan.lib import helpers
from ckan.plugins import toolkit
from dateutil.relativedelta import relativedelta
from flask import Response

from ckanext.feedback.controllers.pagination import get_pagination_value
from ckanext.feedback.models.session import session
from ckanext.feedback.services.admin import aggregation as aggregation_service
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


class AdminController:
    # feedback/admin
    @staticmethod
    @check_administrator
    def admin():
        management_list = [
            {
                'name': _('Approval and Delete'),
                'url': 'feedback.approval-and-delete',
                'description': _(
                    "This is the management screen for approving or deleting "
                    "resource comments, utilization method registration requests, "
                    "and utilization method comments related to "
                    "the organization's resources."
                ),
            },
            {
                'name': _('aggregation'),
                'url': 'feedback.aggregation',
                'description': _(
                    "A screen where users can download aggregated feedback data "
                    "on organizational resources in CSV format."
                ),
            },
        ]

        return toolkit.render(
            'admin/admin.html',
            {'management_list': management_list},
        )

    def get_href(name, active_list):
        if name in active_list:
            active_list.remove(name)
        else:
            active_list.append(name)

        url = f"{toolkit.url_for('feedback.approval-and-delete')}"

        sort_param = request.args.get('sort')
        if sort_param:
            url += f'?sort={sort_param}'

        for active in active_list:
            url += '?' if '?' not in url else '&'
            url += f'filter={active}'

        return url

    def create_filter_dict(filter_set_name, name_label_dict, active_filters, org_list):
        filter_item_list = []
        filter_item_counts = feedback_service.get_feedbacks_total_count(
            filter_set_name,
            active_filters,
            org_list,
        )
        for name, label in name_label_dict.items():
            filter_item = {}
            filter_item["name"] = name
            filter_item["label"] = label
            filter_item["href"] = AdminController.get_href(name, active_filters[:])
            filter_item["count"] = filter_item_counts.get(name, 0)
            filter_item["active"] = (
                False if active_filters == [] else name in active_filters
            )
            if filter_item["count"] > 0:
                filter_item_list.append(filter_item)

        result_filter_item_list = sorted(
            filter_item_list, key=lambda x: x["count"], reverse=True
        )

        return {"type": filter_set_name, "list": result_filter_item_list}

    # feedback/admin/approval-and-delete
    @staticmethod
    @check_administrator
    def approval_and_delete():
        active_filters = request.args.getlist('filter')
        sort = request.args.get('sort', 'newest')

        page, limit, offset, pager_url = get_pagination_value(
            'feedback.approval-and-delete'
        )

        owner_orgs = None
        if not current_user.sysadmin:
            # If the user is not a sysadmin, feedbacks for the organization groups
            # the user is an admin of will be retrieved.
            owner_orgs = current_user.get_group_ids(
                group_type='organization', capacity='admin'
            )
            g.pkg_dict = {
                'organization': {
                    'name': current_user.get_groups(group_type='organization')[0].name,
                }
            }
            org_list = organization_service.get_org_list(owner_orgs)
            feedbacks, total_count = feedback_service.get_feedbacks(
                org_list,
                active_filters=active_filters,
                sort=sort,
                limit=limit,
                offset=offset,
            )
        else:
            # If the user is a sysadmin, all feedbacks
            # will be retrieved regardless of group affiliation.
            org_list = organization_service.get_org_list()
            feedbacks, total_count = feedback_service.get_feedbacks(
                org_list,
                active_filters=active_filters,
                sort=sort,
                limit=limit,
                offset=offset,
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

        if org_list:
            filter_org = {}
            for org in org_list:
                filter_org[org['name']] = org['title']

            filters.append(
                AdminController.create_filter_dict(
                    _('Status'), filter_status, active_filters, org_list
                )
            )
            filters.append(
                AdminController.create_filter_dict(
                    _('Type'), filter_type, active_filters, org_list
                )
            )
            filters.append(
                AdminController.create_filter_dict(
                    _('Organization'), filter_org, active_filters, org_list
                )
            )

        return toolkit.render(
            'admin/approval_and_delete.html',
            {
                "org_list": org_list,
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

    # feedback/admin/approve_target
    @staticmethod
    @check_administrator
    def approve_target():
        resource_comments = request.form.getlist('resource-comments-checkbox')
        utilization = request.form.getlist('utilization-checkbox')
        utilization_comments = request.form.getlist('utilization-comments-checkbox')

        target = 0

        if resource_comments:
            target += AdminController.approve_resource_comments(resource_comments)
        if utilization:
            target += AdminController.approve_utilization(utilization)
        if utilization_comments:
            target += AdminController.approve_utilization_comments(utilization_comments)

        helpers.flash_success(
            f'{target} ' + _('item(s) were approved.'),
            allow_html=True,
        )

        return toolkit.redirect_to('feedback.approval-and-delete')

    # feedback/admin/delete_target
    @staticmethod
    @check_administrator
    def delete_target():
        resource_comments = request.form.getlist('resource-comments-checkbox')
        utilization = request.form.getlist('utilization-checkbox')
        utilization_comments = request.form.getlist('utilization-comments-checkbox')

        target = 0

        if resource_comments:
            target += AdminController.delete_resource_comments(resource_comments)
        if utilization:
            target += AdminController.delete_utilization(utilization)
        if utilization_comments:
            target += AdminController.delete_utilization_comments(utilization_comments)

        helpers.flash_success(
            f'{target} ' + _('item(s) were completely deleted.'),
            allow_html=True,
        )

        return toolkit.redirect_to('feedback.approval-and-delete')

    @staticmethod
    @check_administrator
    def approve_utilization_comments(target):
        target = utilization_comments_service.get_utilization_comment_ids(target)
        utilizations = utilization_service.get_utilizations_by_comment_ids(target)
        AdminController._check_organization_admin_role_with_utilization_comment(
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
        utilizations = utilization_service.get_utilization_details_by_ids(target)
        AdminController._check_organization_admin_role_with_utilization(utilizations)
        resource_ids = utilization_service.get_utilization_resource_ids(target)
        utilization_service.approve_utilization(target, current_user.id)
        utilization_service.refresh_utilization_summary(resource_ids)
        session.commit()

        return len(target)

    @staticmethod
    @check_administrator
    def approve_resource_comments(target):
        target = resource_comments_service.get_resource_comment_ids(target)
        resource_comment_summaries = (
            resource_comments_service.get_resource_comment_summaries(target)
        )
        AdminController._check_organization_admin_role_with_resource(
            resource_comment_summaries
        )
        resource_comments_service.approve_resource_comments(target, current_user.id)
        resource_comments_service.refresh_resources_comments(resource_comment_summaries)
        session.commit()

        return len(target)

    @staticmethod
    @check_administrator
    def delete_utilization_comments(target):
        utilizations = utilization_service.get_utilizations_by_comment_ids(target)
        AdminController._check_organization_admin_role_with_utilization_comment(
            utilizations
        )
        utilization_comments_service.delete_utilization_comments(target)
        utilization_comments_service.refresh_utilizations_comments(utilizations)
        session.commit()

        return len(target)

    @staticmethod
    @check_administrator
    def delete_utilization(target):
        utilizations = utilization_service.get_utilization_details_by_ids(target)
        AdminController._check_organization_admin_role_with_utilization(utilizations)
        resource_ids = utilization_service.get_utilization_resource_ids(target)
        utilization_service.delete_utilization(target)
        utilization_service.refresh_utilization_summary(resource_ids)
        session.commit()

        return len(target)

    @staticmethod
    @check_administrator
    def delete_resource_comments(target):
        resource_comment_summaries = (
            resource_comments_service.get_resource_comment_summaries(target)
        )
        AdminController._check_organization_admin_role_with_resource(
            resource_comment_summaries
        )
        resource_comments_service.delete_resource_comments(target)
        resource_comments_service.refresh_resources_comments(resource_comment_summaries)
        session.commit()

        return len(target)

    @staticmethod
    def _check_organization_admin_role_with_utilization_comment(utilizations):
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
    def _check_organization_admin_role_with_utilization(utilizations):
        for utilization in utilizations:
            if (
                not has_organization_admin_role(utilization)
                and not current_user.sysadmin
            ):
                toolkit.abort(
                    404,
                    _(
                        'The requested URL was not found on the server. '
                        'If you entered the URL manually please check '
                        'your spelling and try again.'
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

    # feedback/admin/aggregation
    @staticmethod
    @check_administrator
    def aggregation():
        today = datetime.now()

        max_month = today.strftime('%Y-%m')
        end_date = today - relativedelta(months=1)
        default_month = end_date.strftime('%Y-%m')

        max_year = today.strftime('%Y')
        year = today - relativedelta(years=1)
        default_year = year.strftime('%Y')

        if not current_user.sysadmin:
            owner_orgs = current_user.get_group_ids(
                group_type='organization', capacity='admin'
            )
            org_list = organization_service.get_org_list(owner_orgs)
        else:
            org_list = organization_service.get_org_list()

        return toolkit.render(
            'admin/aggregation.html',
            {
                "max_month": max_month,
                "default_month": default_month,
                "max_year": int(max_year),
                "default_year": int(default_year),
                "org_list": org_list,
            },
        )

    @staticmethod
    def export_csv_response(results, filename):
        output = io.BytesIO()
        text_wrapper = io.TextIOWrapper(output, encoding='utf-8-sig', newline='')

        try:
            writer = csv.writer(text_wrapper)
            writer.writerow(
                [
                    _("resource_id"),
                    _("group_title"),
                    _("package_title"),
                    _("resource_name"),
                    _("download_count"),
                    _("comment_count"),
                    _("utilization_count"),
                    _("utilization_comment_count"),
                    _("issue_resolution_count"),
                    _("like_count"),
                    _("average_rating"),
                    _("url"),
                ]
            )

            for row in results:
                group_title, package_title, resource_name, resource_link = (
                    aggregation_service.get_resource_details(row.resource_id)
                )

                writer.writerow(
                    [
                        row.resource_id,
                        group_title,
                        package_title,
                        resource_name,
                        row.download,
                        row.resource_comment,
                        row.utilization,
                        row.utilization_comment,
                        row.issue_resolution,
                        row.like,
                        (
                            float(row.rating)
                            if row.rating is not None
                            else _("Not rated")
                        ),
                        resource_link,
                    ]
                )

            text_wrapper.flush()
        finally:
            text_wrapper.detach()

        output.seek(0)

        return Response(
            output,
            mimetype="text/csv charset=utf-8",
            headers={
                "Content-Disposition": (
                    f"attachment; filename*=UTF-8''{filename}; " f"filename={filename}"
                )
            },
        )

    @staticmethod
    @check_administrator
    def download_monthly():
        select_organization_name = request.args.get('group_added')
        select_month = request.args.get('month')

        results = aggregation_service.get_monthly_data(
            select_organization_name, select_month
        )

        year, month = select_month.split("-")
        filename = "{}_{}.csv".format(
            _("feedback_monthly_report"),
            f"{year}{month}",
        )
        encoded_filename = urllib.parse.quote(filename)

        return AdminController.export_csv_response(results, encoded_filename)

    @staticmethod
    @check_administrator
    def download_yearly():
        select_organization_name = request.args.get('group_added')
        select_year = request.args.get('year')

        results = aggregation_service.get_yearly_data(
            select_organization_name, select_year
        )

        filename = "{}_{}.csv".format(
            _("feedback_yearly_report"),
            f"{select_year}",
        )
        encoded_filename = urllib.parse.quote(filename)

        return AdminController.export_csv_response(results, encoded_filename)

    @staticmethod
    @check_administrator
    def download_all_time():
        select_organization_name = request.args.get('group_added')

        results = aggregation_service.get_all_time_data(select_organization_name)

        filename = "{}.csv".format(_("feedback_all_time_report"))
        encoded_filename = urllib.parse.quote(filename)

        return AdminController.export_csv_response(results, encoded_filename)
