import json
import logging
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

log = logging.getLogger(__name__)


class ManagementController:
    # management/comments
    @staticmethod
    @check_administrator
    def comments():
        tab = request.args.get('tab', 'utilization-comments')
        categories = utilization_detail_service.get_utilization_comment_categories()

        limit = config.get('ckan.datasets_per_page')
        offset = 0

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

    # management/get_lead_more_data_comments
    @staticmethod
    @check_administrator
    def get_lead_more_data_comments():
        def custom_converter(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Enum):
                return obj.value
            raise TypeError(f"Type {type(obj)} not serializable")

        data = request.get_json()
        tbody_id = data.get('tbodyId')
        row_count = data.get('rowCount')

        limit = config.get('ckan.datasets_per_page')
        offset = row_count

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
            resources_comment_dict_list = []
            for resource_comment in resource_comments:
                package_dict = resource_comment.resource.package.__dict__
                resource_dict = resource_comment.resource.__dict__

                get_resource_comment_dict = resource_comment.__dict__
                get_resource_comment_dict['resource'] = resource_dict
                get_resource_comment_dict['resource']['package'] = package_dict

                resource_comment_comment_url = toolkit.url_for(
                    'resource_comment.comment',
                    resource_id=get_resource_comment_dict['resource_id'],
                )
                dataset_search_url = toolkit.url_for('dataset.search')

                check_box_dict = {
                    'id': get_resource_comment_dict['id'],
                }
                comments_body_dict = {
                    'url': resource_comment_comment_url,
                    'content': get_resource_comment_dict['content'],
                }
                rating_dict = {
                    'is_enabled_rating': toolkit.asbool(
                        config.get(
                            'ckan.feedback.resources.comment.rating.enable', False
                        )
                    ),
                    'rating': get_resource_comment_dict['rating'],
                }
                organization_dict = {
                    'organization_name': helpers.get_organization(
                        get_resource_comment_dict['resource']['package']['owner_org']
                    )['display_name'],
                }
                dataset_dict = {
                    'url': dataset_search_url,
                    'package_name': get_resource_comment_dict['resource']['package'][
                        'name'
                    ],
                    'package_title': get_resource_comment_dict['resource']['package'][
                        'title'
                    ],
                }
                resource_dict = {
                    'url': dataset_search_url,
                    'package_name': get_resource_comment_dict['resource']['package'][
                        'name'
                    ],
                    'id': get_resource_comment_dict['resource']['id'],
                    'name': get_resource_comment_dict['resource']['name'],
                }
                category_dict = {
                    'category': get_resource_comment_dict['category'],
                }
                created_dict = {
                    'created': get_resource_comment_dict['created'],
                }
                status_dict = {
                    'approval': get_resource_comment_dict['approval'],
                }

                resource_comment_dict = {
                    'check_box': check_box_dict,
                    'comments_body': comments_body_dict,
                    'rating': rating_dict,
                    'organization': organization_dict,
                    'dataset': dataset_dict,
                    'resource': resource_dict,
                    'category': category_dict,
                    'created': created_dict,
                    'status': status_dict,
                    'limit': limit,
                }
                resources_comment_dict_list.append(resource_comment_dict)

            json_output = json.dumps(
                resources_comment_dict_list,
                default=custom_converter,
                ensure_ascii=False,
            )
        else:
            utilization_comment_dict_list = []
            for utilization_comment in utilization_comments:
                package_dict = utilization_comment.utilization.resource.package.__dict__
                resource_dict = utilization_comment.utilization.resource.__dict__
                utilization_dict = utilization_comment.utilization.__dict__

                get_utilization_comment_dict = utilization_comment.__dict__
                get_utilization_comment_dict['utilization'] = utilization_dict
                get_utilization_comment_dict['utilization']['resource'] = resource_dict
                get_utilization_comment_dict['utilization']['resource'][
                    'package'
                ] = package_dict

                utilization_details_url = toolkit.url_for(
                    'utilization.details',
                    utilization_id=get_utilization_comment_dict['utilization_id'],
                )
                dataset_search_url = toolkit.url_for('dataset.search')

                check_box_dict = {
                    'id': get_utilization_comment_dict['id'],
                }
                comments_body_dict = {
                    'url': utilization_details_url,
                    'content': get_utilization_comment_dict['content'],
                }
                utilization_title_dict = {
                    'url': utilization_details_url,
                    'title': get_utilization_comment_dict['utilization']['title'],
                }
                organization_dict = {
                    'organization_name': helpers.get_organization(
                        get_utilization_comment_dict['utilization']['resource'][
                            'package'
                        ]['owner_org']
                    )['display_name'],
                }
                dataset_dict = {
                    'url': dataset_search_url,
                    'package_name': get_utilization_comment_dict['utilization'][
                        'resource'
                    ]['package']['name'],
                    'package_title': get_utilization_comment_dict['utilization'][
                        'resource'
                    ]['package']['title'],
                }
                resource_dict = {
                    'url': dataset_search_url,
                    'package_name': get_utilization_comment_dict['utilization'][
                        'resource'
                    ]['package']['name'],
                    'id': get_utilization_comment_dict['utilization']['resource']['id'],
                    'name': get_utilization_comment_dict['utilization']['resource'][
                        'name'
                    ],
                }
                category_dict = {
                    'category': get_utilization_comment_dict['category'],
                }
                created_dict = {
                    'created': get_utilization_comment_dict['created'],
                }
                status_dict = {
                    'approval': get_utilization_comment_dict['approval'],
                }

                utilization_comment_dict = {
                    'check_box': check_box_dict,
                    'comments_body': comments_body_dict,
                    'utilization_title': utilization_title_dict,
                    'organization': organization_dict,
                    'dataset': dataset_dict,
                    'resource': resource_dict,
                    'category': category_dict,
                    'created': created_dict,
                    'status': status_dict,
                    'limit': limit,
                }
                utilization_comment_dict_list.append(utilization_comment_dict)

            json_output = json.dumps(
                utilization_comment_dict_list,
                default=custom_converter,
                ensure_ascii=False,
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
