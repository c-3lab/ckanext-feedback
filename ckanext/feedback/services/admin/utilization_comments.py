from datetime import datetime

from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import literal

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization, UtilizationComment


def get_utilization_comments_query(org_list):
    org_names = [org['name'] for org in org_list]

    query = (
        session.query(
            Group.name.label('group_name'),
            Package.name.label('package_name'),
            Package.title.label('package_title'),
            Package.owner_org.label('owner_org'),
            Resource.id.label('resource_id'),
            Resource.name.label('resource_name'),
            Utilization.id.label('utilization_id'),
            literal('利活用コメント').label('feedback_type'),
            UtilizationComment.id.label('comment_id'),
            UtilizationComment.content.label('content'),
            UtilizationComment.created.label('created'),
            UtilizationComment.approval.label('is_approved'),
        )
        .select_from(Package)
        .join(Group, Package.owner_org == Group.id)
        .join(Resource)
        .join(Utilization)
        .join(UtilizationComment)
        .filter(
            Group.name.in_(org_names),
            Package.state == "active",
            Resource.state == "active",
        )
    )

    return query


def get_simple_utilization_comments_query(org_list):
    org_names = [org['name'] for org in org_list]

    query = (
        session.query(
            Group.name.label('group_name'),
            literal("利活用コメント").label("feedback_type"),
            UtilizationComment.approval.label('is_approved'),
        )
        .join(Package, Group.id == Package.owner_org)
        .join(Resource, Package.id == Resource.package_id)
        .join(Utilization, Resource.id == Utilization.resource_id)
        .join(UtilizationComment, Utilization.id == UtilizationComment.utilization_id)
        .filter(
            Group.name.in_(org_names),
            Package.state == "active",
            Resource.state == "active",
        )
    )

    return query


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


# Get the IDs of utilization_comments where approval is False using comment_id_list.
def get_utilization_comment_ids(comment_id_list):
    query = (
        session.query(UtilizationComment.id)
        .filter(UtilizationComment.id.in_(comment_id_list))
        .filter(~UtilizationComment.approval)
    )

    comment_ids = [comment.id for comment in query.all()]

    return comment_ids


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
