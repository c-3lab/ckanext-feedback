import json
from datetime import datetime
from enum import Enum

from ckan.common import _, config, current_user, g, request
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
    @staticmethod
    def _limit_and_offset_settings(limit, offset):
        return limit, offset

    # management/comments
    @staticmethod
    @check_administrator
    def comments():
        tab = request.args.get('tab', 'utilization-comments')
        categories = utilization_detail_service.get_utilization_comment_categories()

        limit, offset = ManagementController._limit_and_offset_settings(
            config.get('ckan.datasets_per_page'), 0
        )

        # If user is organization admin
        if not current_user.sysadmin:
            ids = current_user.get_group_ids(
                group_type='organization', capacity='admin'
            )
            resource_comments, max_resource_count = (
                resource_comment_service.get_resource_comments(
                    owner_orgs=ids, limit=limit, offset=offset
                )
            )
            utilization_comments, max_utilization_count = (
                utilization_detail_service.get_utilization_comments(
                    owner_orgs=ids, limit=limit, offset=offset
                )
            )
            g.pkg_dict = {
                'organization': {
                    'name': current_user.get_groups(group_type='organization')[0].name,
                }
            }
        else:
            resource_comments, max_resource_count = (
                resource_comment_service.get_resource_comments(
                    limit=limit, offset=offset
                )
            )
            utilization_comments, max_utilization_count = (
                utilization_detail_service.get_utilization_comments(
                    limit=limit, offset=offset
                )
            )
        return toolkit.render(
            'management/comments.html',
            {
                'categories': categories,
                'utilization_comments': utilization_comments,
                'resource_comments': resource_comments,
                'tab': tab,
                'max_resource_count': max_resource_count,
                'max_utilization_count': max_utilization_count,
                'limit': limit,
            },
        )

    @staticmethod
    def _custom_converter(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        raise TypeError(f"Type {type(obj)} not serializable")

    @staticmethod
    def _convert_to_json(tbody_id, comments_data, limit):
        dict_list = []
        for comment_data in comments_data:
            if tbody_id == 'resource-comments-table-body':
                package_dict = comment_data.resource.package.__dict__
                resource_dict = comment_data.resource.__dict__
                comment_data_dict = comment_data.__dict__
                comment_info_block = comment_data_dict
                url = toolkit.url_for(
                    'resource_comment.comment',
                    resource_id=comment_data_dict['resource_id'],
                )
            else:
                package_dict = comment_data.utilization.resource.package.__dict__
                resource_dict = comment_data.utilization.resource.__dict__
                utilization_dict = comment_data.utilization.__dict__
                comment_data_dict = comment_data.__dict__
                comment_data_dict['utilization'] = utilization_dict
                comment_info_block = comment_data_dict['utilization']
                url = toolkit.url_for(
                    'utilization.details',
                    utilization_id=comment_data_dict['utilization_id'],
                )

            comment_info_block['resource'] = resource_dict
            comment_info_block['resource']['package'] = package_dict

            dataset_search_url = toolkit.url_for('dataset.search')

            comment_dict = {
                'check_box': {
                    'id': comment_data_dict['id'],
                },
                'comments_body': {
                    'url': url,
                    'content': comment_data_dict['content'],
                },
                'organization': {
                    'organization_name': helpers.get_organization(
                        comment_info_block['resource']['package']['owner_org']
                    )['display_name'],
                },
                'dataset': {
                    'url': dataset_search_url,
                    'package_name': comment_info_block['resource']['package']['name'],
                    'package_title': comment_info_block['resource']['package']['title'],
                },
                'resource': {
                    'url': dataset_search_url,
                    'package_name': comment_info_block['resource']['package']['name'],
                    'id': comment_info_block['resource']['id'],
                    'name': comment_info_block['resource']['name'],
                },
                'category': {
                    'category': comment_data_dict['category'],
                },
                'created': {
                    'created': comment_data_dict['created'],
                },
                'status': {
                    'approval': comment_data_dict['approval'],
                },
                'limit': limit,
            }
            if tbody_id == 'resource-comments-table-body':
                comment_dict['rating'] = (
                    {
                        'is_enabled_rating': toolkit.asbool(
                            config.get(
                                'ckan.feedback.resources.comment.rating.enable', False
                            )
                        ),
                        'rating': comment_data_dict['rating'],
                    },
                )
            else:
                comment_dict['utilization_title'] = {
                    'url': url,
                    'title': comment_info_block['title'],
                }

            dict_list.append(comment_dict)

        json_output = json.dumps(
            dict_list,
            default=ManagementController._custom_converter,
            ensure_ascii=False,
        )

        return json_output

    # management/get_lead_more_data_comments
    @staticmethod
    @check_administrator
    def get_lead_more_data_comments():
        data = request.get_json()
        tbody_id = data.get('tbodyId')
        row_count = data.get('rowCount')

        limit, offset = ManagementController._limit_and_offset_settings(
            config.get('ckan.datasets_per_page'), row_count
        )

        if not current_user.sysadmin:
            ids = current_user.get_group_ids(
                group_type='organization', capacity='admin'
            )
            if tbody_id == 'resource-comments-table-body':
                resource_comments, total_count = (
                    resource_comment_service.get_resource_comments(
                        owner_orgs=ids, limit=limit, offset=offset
                    )
                )
            else:
                utilization_comments, total_count = (
                    utilization_detail_service.get_utilization_comments(
                        owner_orgs=ids, limit=limit, offset=offset
                    )
                )
            g.pkg_dict = {
                'organization': {
                    'name': current_user.get_groups(group_type='organization')[0].name,
                }
            }
        else:
            if tbody_id == 'resource-comments-table-body':
                resource_comments, total_count = (
                    resource_comment_service.get_resource_comments(
                        limit=limit, offset=offset
                    )
                )
            else:
                utilization_comments, total_count = (
                    utilization_detail_service.get_utilization_comments(
                        limit=limit, offset=offset
                    )
                )

        if tbody_id == 'resource-comments-table-body':
            json_output = ManagementController._convert_to_json(
                tbody_id, resource_comments, limit
            )
        else:
            json_output = ManagementController._convert_to_json(
                tbody_id, utilization_comments, limit
            )
        return json_output

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
