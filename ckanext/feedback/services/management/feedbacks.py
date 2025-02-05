import logging

from sqlalchemy import func, select, union_all
from sqlalchemy.sql import and_, or_

from ckanext.feedback.models.session import session
from ckanext.feedback.services.management import (
    resource_comments as resource_comments_service,
)
from ckanext.feedback.services.management import utilization as utilization_service
from ckanext.feedback.services.management import (
    utilization_comments as utilization_comments_service,
)
from ckanext.feedback.services.organization import organization as organization_service

log = logging.getLogger(__name__)


def get_feedbacks(
    owner_orgs=None,
    active_filters=None,
    sort=None,
    limit=None,
    offset=None,
):
    """
    Retrieves a list of feedback items based on various filters, sorting,
    and pagination options.

    Args:
        owner_orgs (list, optional): List of owner organization IDs to filter feedback.
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
    """

    resource_comments = resource_comments_service.get_resource_comments_query()
    utilizations = utilization_service.get_utilizations_query()
    utilization_comments = utilization_comments_service.get_utilization_comments_query()

    combined_query = union_all(resource_comments, utilizations, utilization_comments)
    combined_subquery = combined_query.subquery()

    query = select(combined_subquery)

    if owner_orgs is not None:
        query = query.where(combined_subquery.c.owner_org.in_(owner_orgs))

    if active_filters is not None:
        filter_status = []
        if 'approved' in active_filters:
            filter_status.append(combined_subquery.c.is_approved.is_(True))
        if 'unapproved' in active_filters:
            filter_status.append(combined_subquery.c.is_approved.is_(False))

        filter_type = []
        if 'resource' in active_filters:
            filter_type.append(combined_subquery.c.feedback_type == 'リソースコメント')
        if 'utilization' in active_filters:
            filter_type.append(combined_subquery.c.feedback_type == '利活用申請')
        if 'util-comment' in active_filters:
            filter_type.append(combined_subquery.c.feedback_type == '利活用コメント')

        org_list = []
        if owner_orgs is not None:
            org_list = organization_service.get_org_list(owner_orgs)
        else:
            org_list = organization_service.get_org_list()

        filter_org = []
        for org in org_list:
            if org['name'] in active_filters:
                filter_org.append(combined_subquery.c.group_name == org['name'])

        filter_conditions = []
        if filter_status:
            filter_conditions.append(or_(*filter_status))
        if filter_type:
            filter_conditions.append(or_(*filter_type))
        if filter_org:
            filter_conditions.append(or_(*filter_org))

        if filter_conditions:
            query = query.where(and_(*filter_conditions))

    if sort is not None:
        if sort == 'newest':
            query = query.order_by(combined_subquery.c.created.desc())
        elif sort == 'oldest':
            query = query.order_by(combined_subquery.c.created)
        elif sort == 'dataset_asc':
            query = query.order_by(
                combined_subquery.c.package_name, combined_subquery.c.resource_name
            )
        elif sort == 'dataset_desc':
            query = query.order_by(
                combined_subquery.c.package_name.desc(),
                combined_subquery.c.resource_name,
            )
        elif sort == 'resource_asc':
            query = query.order_by(
                combined_subquery.c.resource_name, combined_subquery.c.package_name
            )
        elif sort == 'resource_desc':
            query = query.order_by(
                combined_subquery.c.resource_name.desc(),
                combined_subquery.c.package_name,
            )

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.execute(count_query).scalar()

    if limit is not None and offset is not None:
        query = query.limit(limit)
        query = query.offset(offset)

    results = session.execute(query).fetchall()

    feedback_list = []
    for result in results:
        feedback = {
            'package_name': result.package_name,
            'package_title': result.package_title,
            'resource_id': result.resource_id,
            'resource_name': result.resource_name,
            'utilization_id': result.utilization_id,
            'feedback_type': result.feedback_type,
            'comment_id': result.comment_id,
            'content': result.content,
            'created': result.created,
            'is_approved': result.is_approved,
        }
        feedback_list.append(feedback)

    return feedback_list, total_count


def get_feedbacks_count(owner_orgs, active_filters):
    feedback_list, total_count = get_feedbacks(
        owner_orgs=owner_orgs, active_filters=[active_filters]
    )
    return total_count
