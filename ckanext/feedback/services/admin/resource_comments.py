from datetime import datetime

from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import func, literal

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentSummary,
)
from ckanext.feedback.models.session import session


def get_resource_comments_query(org_list):
    org_names = [org['name'] for org in org_list]

    query = (
        session.query(
            Group.name.label('group_name'),
            Package.name.label('package_name'),
            Package.title.label('package_title'),
            Package.owner_org.label('owner_org'),
            Resource.id.label('resource_id'),
            Resource.name.label('resource_name'),
            literal(None).label('utilization_id'),
            literal('リソースコメント').label('feedback_type'),
            ResourceComment.id.label('comment_id'),
            ResourceComment.content.label('content'),
            ResourceComment.created.label('created'),
            ResourceComment.approval.label('is_approved'),
        )
        .select_from(Package)
        .join(Group, Package.owner_org == Group.id)
        .join(Resource)
        .join(ResourceComment)
        .filter(
            Group.name.in_(org_names),
            Package.state == "active",
            Resource.state == "active",
        )
    )

    return query


def get_simple_resource_comments_query(org_list):
    org_names = [org['name'] for org in org_list]

    query = (
        session.query(
            Group.name.label('group_name'),
            literal("リソースコメント").label("feedback_type"),
            ResourceComment.approval.label('is_approved'),
        )
        .join(Package, Group.id == Package.owner_org)
        .join(Resource, Package.id == Resource.package_id)
        .join(ResourceComment, Resource.id == ResourceComment.resource_id)
        .filter(
            Group.name.in_(org_names),
            Package.state == "active",
            Resource.state == "active",
        )
    )

    return query


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
