from datetime import datetime

from ckan.common import config
from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import desc, func

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentSummary,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization, UtilizationComment


# Get approval utilization comment count using utilization.id
def get_utilization_comments(utilization_id):
    count = (
        session.query(UtilizationComment)
        .filter(
            UtilizationComment.utilization_id == utilization_id,
            UtilizationComment.approval,
        )
        .count()
    )
    return count


# Get utilizations using comment_id_list
def get_utilizations(comment_id_list):
    utilizations = (
        session.query(Utilization)
        .join(UtilizationComment)
        .filter(UtilizationComment.id.in_(comment_id_list))
    ).all()
    return utilizations


# Get the IDs of utilization where approval is False using utilization_id_list.
def get_utilization_ids(utilization_id_list):
    query = (
        session.query(Utilization.id)
        .filter(Utilization.id.in_(utilization_id_list))
        .filter(~Utilization.approval)
    )

    utilization_ids = [utilization.id for utilization in query.all()]

    return utilization_ids


# Get the IDs of utilization_comments where approval is False using comment_id_list.
def get_utilization_comment_ids(comment_id_list):
    query = (
        session.query(UtilizationComment.id)
        .filter(UtilizationComment.id.in_(comment_id_list))
        .filter(~UtilizationComment.approval)
    )

    comment_ids = [comment.id for comment in query.all()]

    return comment_ids


# Get organization using owner_org
def get_organization(owner_org):
    organization = session.query(Group).filter(Group.id == owner_org).first()
    return organization


# Recalculate total approved bulk utilizations comments
def refresh_utilizations_comments(utilizations):
    session.bulk_update_mappings(
        Utilization,
        [
            {
                'id': utilization.id,
                'comment': get_utilization_comments(utilization.id),
                'updated': datetime.now(),
            }
            for utilization in utilizations
        ],
    )


# Get the IDs of resource_comments where approval is False using comment_id_list.
def get_resource_comment_ids(comment_id_list):
    query = (
        session.query(ResourceComment.id)
        .filter(ResourceComment.id.in_(comment_id_list))
        .filter(~ResourceComment.approval)
    )

    comment_ids = [comment.id for comment in query.all()]

    return comment_ids


# Get resource comment summaries using comment_id_list
def get_resource_comment_summaries(comment_id_list):
    resource_comment_summaries = (
        session.query(ResourceCommentSummary)
        .join(Resource)
        .join(ResourceComment)
        .filter(ResourceComment.id.in_(comment_id_list))
    ).all()
    return resource_comment_summaries


def get_non_approve_contests(owner_orgs=None, limit=None, offset=None):
    resource_comments = session.query(
        ResourceComment.id,
        ResourceComment.resource.package.name.label('dataset_title'),
        ResourceComment.resource.name.label('resource_title'),
        ResourceComment.content.label('content'),
        ResourceComment.approval,
    ).filter(ResourceComment.approval is False)
    if owner_orgs is not None:
        resource_comments = (
            resource_comments.join(Resource)
            .join(Package)
            .filter(Package.owner_org.in_(owner_orgs))
        )

    utilizations = session.query(
        Utilization.id,
        Utilization.resource.package.name.label('dataset_title'),
        Utilization.resource.resource.name.label('resource_title'),
        Utilization.title.label('content'),
        Utilization.approval,
    ).filter(Utilization.approval is False)
    if owner_orgs is not None:
        utilizations = utilizations.join(Package).filter(
            Package.owner_org.in_(owner_orgs)
        )

    utilization_comments = session.query(
        UtilizationComment.id,
        UtilizationComment.utilization.resource.package.name.label('dataset_title'),
        UtilizationComment.utilization.resource.resource.name.label('resource_title'),
        UtilizationComment.utilization.title.label('content'),
        UtilizationComment.approval,
    ).filter(UtilizationComment.approval is False)
    if owner_orgs is not None:
        utilization_comments = (
            utilization_comments.join(Utilization)
            .join(Resource)
            .join(Package)
            .filter(Package.owner_org.in_(owner_orgs))
        )

    union_query = resource_comments.union_all(utilizations)
    union_query = union_query.union_all(utilization_comments)
    results = union_query.limit(limit).offset(offset).all()
    if limit is not None or offset is not None:
        total_count = union_query.count()
        return results, total_count
    return results


# Recalculate total approved bulk resources comments
def refresh_resources_comments(resource_comment_summaries):
    mappings = []
    for resource_comment_summary in resource_comment_summaries:
        row = (
            session.query(
                func.sum(ResourceComment.rating).label('total_rating'),
                func.count().label('total_comment'),
                func.count(ResourceComment.rating).label('total_rating_comment'),
            )
            .filter(
                ResourceComment.resource_id == resource_comment_summary.resource.id,
                ResourceComment.approval,
            )
            .first()
        )
        if row.total_rating is None:
            rating = 0
        else:
            rating = row.total_rating / row.total_rating_comment
        mappings.append(
            {
                'id': resource_comment_summary.id,
                'comment': row.total_comment,
                'rating_comment': row.total_rating_comment,
                'rating': rating,
                'updated': datetime.now(),
            }
        )
    session.bulk_update_mappings(ResourceCommentSummary, mappings)


# Approve selected utilization comments
def approve_utilization_comments(comment_id_list, approval_user_id):
    session.bulk_update_mappings(
        UtilizationComment,
        [
            {
                'id': comment_id,
                'approval': True,
                'approved': datetime.now(),
                'approval_user_id': approval_user_id,
            }
            for comment_id in comment_id_list
        ],
    )


# Delete selected utilization comments
def delete_utilization_comments(comment_id_list):
    (
        session.query(UtilizationComment)
        .filter(UtilizationComment.id.in_(comment_id_list))
        .delete(synchronize_session='fetch')
    )


# Approve selected resource comments
def approve_resource_comments(comment_id_list, approval_user_id):
    session.bulk_update_mappings(
        ResourceComment,
        [
            {
                'id': comment_id,
                'approval': True,
                'approved': datetime.now(),
                'approval_user_id': approval_user_id,
            }
            for comment_id in comment_id_list
        ],
    )


# Delete selected resource comments
def delete_resource_comments(comment_id_list):
    (
        session.query(ResourceComment)
        .filter(ResourceComment.id.in_(comment_id_list))
        .delete(synchronize_session='fetch')
    )


# Get the number of pages of selected resource comments
def get_page_for_resource_comment(resource_id, resource_comment_id):
    comments_per_page = config.get('ckan.datasets_per_page')

    #
    # Note: Ensure that the `order_by` used in this query is consistent
    # with the `order_by` in the get_resource_comments function.
    # The ordering must be the same for both functions.
    #
    query = (
        session.query(
            ResourceComment.id,
            func.row_number()
            .over(order_by=desc(ResourceComment.created))
            .label('row_num'),
        )
        .filter(ResourceComment.resource_id == resource_id)
        .subquery()
    )

    row_number = (
        session.query(query.c.row_num)
        .filter(query.c.id == resource_comment_id)
        .scalar()
    )

    page_number = (row_number - 1) // comments_per_page + 1

    return page_number


# Get the number of pages of selected utilization comments
def get_page_for_utilization_comment(utilization_id, utilization_comment_id):
    comments_per_page = config.get('ckan.datasets_per_page')

    query = (
        session.query(
            UtilizationComment.id,
            func.row_number()
            .over(order_by=desc(UtilizationComment.created))
            .label('row_num'),
        )
        .filter(UtilizationComment.utilization_id == utilization_id)
        .subquery()
    )

    row_number = (
        session.query(query.c.row_num)
        .filter(query.c.id == utilization_comment_id)
        .scalar()
    )

    page_number = (row_number - 1) // comments_per_page + 1

    return page_number
