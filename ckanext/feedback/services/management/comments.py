from datetime import datetime

from ckan.model.group import Group
from ckan.model.resource import Resource
from sqlalchemy import func

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


# Get resource comment summaries using comment_id_list
def get_resource_comment_summaries(comment_id_list):
    resource_comment_summaries = (
        session.query(ResourceCommentSummary)
        .join(Resource)
        .join(ResourceComment)
        .filter(ResourceComment.id.in_(comment_id_list))
    ).all()
    return resource_comment_summaries


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
