import logging

from ckan.common import _
from sqlalchemy import case, func, select, union_all
from sqlalchemy.sql import and_

from ckanext.feedback.models.session import session
from ckanext.feedback.services.admin import (
    resource_comments as resource_comments_service,
)
from ckanext.feedback.services.admin import utilization as utilization_service
from ckanext.feedback.services.admin import (
    utilization_comments as utilization_comments_service,
)

log = logging.getLogger(__name__)


def apply_filters_to_query(query, active_filters, org_list, combined_query):
    if active_filters:
        filter_conditions = []

        filter_status = []
        if 'approved' in active_filters:
            filter_status.append(combined_query.c.is_approved.is_(True))
        if 'unapproved' in active_filters:
            filter_status.append(combined_query.c.is_approved.is_(False))
        if filter_status:
            filter_conditions.append(and_(*filter_status))

        filter_type = []
        if 'resource' in active_filters:
            filter_type.append(combined_query.c.feedback_type == 'リソースコメント')
        if 'utilization' in active_filters:
            filter_type.append(combined_query.c.feedback_type == '利活用申請')
        if 'util-comment' in active_filters:
            filter_type.append(combined_query.c.feedback_type == '利活用コメント')
        if filter_type:
            filter_conditions.append(and_(*filter_type))

        filter_org = [
            combined_query.c.group_name == org['name']
            for org in org_list
            if org['name'] in active_filters
        ]
        if filter_org:
            filter_conditions.append(and_(*filter_org))

        if filter_conditions:
            query = query.filter(and_(*filter_conditions))

    return query


def get_feedbacks(
    org_list,
    active_filters=None,
    sort=None,
    limit=None,
    offset=None,
):
    """
    Retrieves a list of feedback items based on various filters, sorting,
    and pagination options.

    Args:
        org_list (list): List of dictionaries containing owner
        organization information.
            Options are:
                - 'name': Organization name
                - 'title': Organization title
        active_filters (list, optional): List of filters to apply.
            Supported filters:
                - 'approved': Only include approved feedback.
                - 'unapproved': Only include unapproved feedback.
                - 'resource': Include feedback of type 'resource comment'.
                - 'utilization': Include feedback of type 'utilization request'.
                - 'util-comment': Include feedback of type 'utilization comment'.
                - Organization names can also be used to filter by specific groups.
        sort (str, optional): Sorting order for the feedback.
            Options are:
                - 'newest': Sort by creation date (newest first).
                - 'oldest': Sort by creation date (oldest first).
                - 'dataset_asc': Sort by dataset name (ascending).
                - 'dataset_desc': Sort by dataset name (descending).
                - 'resource_asc': Sort by resource name (ascending).
                - 'resource_desc': Sort by resource name (descending).
        limit (int, optional): Maximum number of feedback items to retrieve.
        offset (int, optional): Number of feedback items to skip for pagination.

    Returns:
        list[dict]: A list of feedback items, where each item is represented
        as a dictionary containing the following keys:
            - 'package_name': Name of the dataset the feedback belongs to.
            - 'package_title': Title of the dataset the feedback belongs to.
            - 'resource_id': ID of the resource the feedback refers to.
            - 'resource_name': Name of the resource the feedback refers to.
            - 'utilization_id': ID of the utilization request (if applicable).
            - 'feedback_type': Type of the feedback
            ('resource comment', 'utilization request', or 'utilization comment').
            - 'comment_id': ID of the comment (if applicable).
            - 'content': The actual feedback content.
            - 'created': The creation timestamp of the feedback.
            - 'is_approved': Approval status of the feedback.
        total_count: Returns the number of cases obtained.
        No limit on the number of rows.
    """
    resource_comments = resource_comments_service.get_resource_comments_query(org_list)
    utilizations = utilization_service.get_utilizations_query(org_list)
    utilization_comments = utilization_comments_service.get_utilization_comments_query(
        org_list
    )

    combined_query = union_all(
        resource_comments, utilizations, utilization_comments
    ).subquery()

    query = select(combined_query)

    query = apply_filters_to_query(query, active_filters, org_list, combined_query)

    sort_map = {
        'newest': [combined_query.c.created.desc()],
        'oldest': [combined_query.c.created],
        'dataset_asc': [combined_query.c.package_name, combined_query.c.resource_name],
        'dataset_desc': [
            combined_query.c.package_name.desc(),
            combined_query.c.resource_name,
        ],
        'resource_asc': [combined_query.c.resource_name, combined_query.c.package_name],
        'resource_desc': [
            combined_query.c.resource_name.desc(),
            combined_query.c.package_name,
        ],
    }

    if sort in sort_map:
        query = query.order_by(*sort_map[sort])

    count_query = select(func.count()).select_from(query)
    total_count = session.execute(count_query).scalar()

    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)

    results = session.execute(query).fetchall()

    feedback_list = [
        {
            col: getattr(result, col)
            for col in [
                'package_name',
                'package_title',
                'resource_id',
                'resource_name',
                'utilization_id',
                'feedback_type',
                'comment_id',
                'content',
                'created',
                'is_approved',
            ]
        }
        for result in results
    ]

    return feedback_list, total_count


def get_approval_counts(active_filters, org_list, combined_query):
    query = session.query(
        func.count(case((combined_query.c.is_approved, 1))).label("approved"),
        func.count(case((~combined_query.c.is_approved, 1))).label("unapproved"),
    )

    query = apply_filters_to_query(query, active_filters, org_list, combined_query)

    results = query.one()

    return {"approved": results.approved, "unapproved": results.unapproved}


def get_type_counts(active_filters, org_list, combined_query):
    query = session.query(
        func.count(
            case((combined_query.c.feedback_type == "リソースコメント", 1))
        ).label("resource"),
        func.count(case((combined_query.c.feedback_type == "利活用申請", 1))).label(
            "utilization"
        ),
        func.count(case((combined_query.c.feedback_type == "利活用コメント", 1))).label(
            "util_comment"
        ),
    )

    query = apply_filters_to_query(query, active_filters, org_list, combined_query)

    results = query.one()

    return {
        "resource": results.resource,
        "utilization": results.utilization,
        "util-comment": results.util_comment,
    }


def get_organization_counts(active_filters, org_list, combined_query):
    columns = [
        func.count(case((combined_query.c.group_name == org["name"], 1))).label(
            org["title"]
        )
        for org in org_list
    ]

    query = session.query(*columns)

    query = apply_filters_to_query(query, active_filters, org_list, combined_query)

    results = query.one()

    return {org['name']: results[org["title"]] for org in org_list}


def get_feedbacks_total_count(filter_set_name, active_filters, org_list):
    resource_comment_query = (
        resource_comments_service.get_simple_resource_comments_query(org_list)
    )
    utilization_query = utilization_service.get_simple_utilizations_query(org_list)
    utilization_comment_query = (
        utilization_comments_service.get_simple_utilization_comments_query(org_list)
    )

    combined_query = union_all(
        resource_comment_query, utilization_query, utilization_comment_query
    )

    if filter_set_name == _('Status'):
        return get_approval_counts(active_filters, org_list, combined_query)
    elif filter_set_name == _('Type'):
        return get_type_counts(active_filters, org_list, combined_query)
    elif filter_set_name == _('Organization'):
        return get_organization_counts(active_filters, org_list, combined_query)
