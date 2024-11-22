from ckan.common import _, current_user, g, request
from ckan.lib import helpers
from ckan.plugins import toolkit

import ckanext.feedback.services.management.comments as comments_service
import ckanext.feedback.services.resource.comment as resource_comment_service
import ckanext.feedback.services.utilization.details as utilization_detail_service
import ckanext.feedback.services.utilization.search as search_service
from ckanext.feedback.controllers.pagination import get_pagination_value
from ckanext.feedback.models.session import session
from ckanext.feedback.services.common.check import (
    check_administrator,
    has_organization_admin_role,
)


class ManagementController:
    # management/comments
    @staticmethod
    @check_administrator
    def admin():
        def get_href(name, active_list):
            if name in active_list:
                # 無効化
                active_list.remove(name)
            else:
                # 有効化
                active_list.append(name)

            url = f"{toolkit.url_for('management.comments')}"
            for active in active_list:
                url += '?' if 'filter-name=' not in url else '&'
                url += f'filter-name={active}'
            return url

        def create_filter_dict(filter_set_name, name_label_dict, active_filters):
            filter_item_list = []
            for name, label in name_label_dict.items():
                filter_item = {}
                filter_item["name"] = name
                filter_item["label"] = label
                filter_item["href"] = get_href(name, active_filters[:])
                filter_item["count"] = '0'  # TODO: 値取得して設定
                filter_item["active"] = (
                    False if active_filters == [] else name in active_filters
                )
                filter_item_list.append(filter_item)
            return {"type": filter_set_name, "list": filter_item_list}

        active_filters = request.args.getlist('filter-name')
        filter_data = {
            "resource": "リソースコメント",
            "utilization": "利活用申請",
            "util-comment": "利活用コメント",
        }

        filters = []
        filters.append(create_filter_dict("申請種類", filter_data, active_filters))
        data_list = []

        page, limit, offset, pager_url = get_pagination_value('utilization.search')

        # If user is organization admin
        admin_owner_orgs = None
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
            admin_owner_orgs = current_user.get_group_ids(
                group_type='organization', capacity='admin'
            )
        else:
            resource_comments = resource_comment_service.get_resource_comments()
            utilization_comments = utilization_detail_service.get_utilization_comments()

        # resource_comments
        if active_filters == [] or 'resource' in active_filters:
            for resource_comment in resource_comments:
                resource_id = resource_comment.id
                dataset_url = (
                    toolkit.url_for('dataset.search')
                    + resource_comment.resource.package.name
                )
                resource_url = dataset_url + "/resource/" + resource_comment.resource.id
                data = {
                    "id": resource_id,
                    "dataset_title": resource_comment.resource.package.name,
                    "dataset_url": dataset_url,
                    "resource_title": resource_comment.resource.name,
                    "resource_url": resource_url,
                    "target_type": "リソースコメント",
                    "target_url": toolkit.url_for(
                        'resource_comment.comment',
                        resource_id=resource_comment.resource.id,
                    ),
                    "content": resource_comment.content,
                }
                data_list.append(data)

        # utilizations
        utilizations, total_count = search_service.get_utilizations(
            approval=False,
            admin_owner_orgs=admin_owner_orgs,
            limit=limit,
            offset=offset,
        )
        if active_filters == [] or 'utilization' in active_filters:
            for utilization in utilizations:
                resource_id = utilization.resource_id
                utilization_id = utilization.id
                dataset_url = (
                    toolkit.url_for('dataset.search') + utilization.package_name
                )
                resource_url = dataset_url + "/resource/" + utilization.resource_id
                data = {
                    "id": utilization.id,
                    "dataset_title": utilization.package_name,
                    "dataset_url": dataset_url,
                    "resource_title": utilization.resource_name,
                    "resource_url": resource_url,
                    "target_type": "利活用申請",
                    "target_url": toolkit.url_for(
                        'utilization.details', utilization_id=utilization_id
                    ),
                    "content": utilization.title,
                }
                data_list.append(data)

        # utilization_comments
        if active_filters == [] or 'util-comment' in active_filters:
            for utilization_comment in utilization_comments:
                resource_id = utilization_comment.utilization.resource_id
                utilization_id = utilization_comment.utilization_id
                dataset_url = (
                    toolkit.url_for('dataset.search')
                    + utilization_comment.utilization.resource.package.name
                )
                resource_url = (
                    dataset_url
                    + "/resource/"
                    + utilization_comment.utilization.resource.id
                )
                data = {
                    "id": utilization_comment.id,
                    "dataset_title": (
                        utilization_comment.utilization.resource.package.name
                    ),
                    "dataset_url": dataset_url,
                    "resource_title": utilization_comment.utilization.resource.name,
                    "resource_url": resource_url,
                    "target_type": "利活用コメント",
                    "target_url": toolkit.url_for(
                        'utilization.details', utilization_id=utilization_id
                    ),
                    "content": utilization_comment.content,
                }
                data_list.append(data)

        return toolkit.render(
            # 'management/admin.html',{},
            # 'management/feedback_status.html',{},
            'management/feedback_status_list.html',
            {
                "data_list": data_list,
                "filters": filters,
                'page': helpers.Page(
                    collection=utilizations,
                    page=page,
                    url=pager_url,
                    item_count=total_count,
                    # items_per_page=limit,
                    items_per_page=2,
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
        return toolkit.redirect_to('management.comments', tab='utilization-comments')

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
        return toolkit.redirect_to('management.comments', tab='resource-comments')

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
        return toolkit.redirect_to('management.comments', tab='utilization-comments')

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
        return toolkit.redirect_to('management.comments', tab='resource-comments')

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
