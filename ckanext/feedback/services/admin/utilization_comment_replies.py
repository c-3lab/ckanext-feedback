from datetime import datetime

from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import literal

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentReply,
)


def get_utilization_comment_replies_query(org_list):
    org_names = [org['name'] for org in org_list]

    return (
        session.query(
            Group.name.label('group_name'),
            Package.name.label('package_name'),
            Package.title.label('package_title'),
            Package.owner_org.label('owner_org'),
            Resource.id.label('resource_id'),
            Resource.name.label('resource_name'),
            Utilization.id.label('utilization_id'),
            literal('utilization_comment_reply').label('feedback_type'),
            UtilizationCommentReply.id.label('comment_id'),
            UtilizationCommentReply.content.label('content'),
            UtilizationCommentReply.created.label('created'),
            UtilizationCommentReply.approval.label('is_approved'),
        )
        .select_from(Package)
        .join(Group, Package.owner_org == Group.id)
        .join(Resource, Package.id == Resource.package_id)
        .join(Utilization, Resource.id == Utilization.resource_id)
        .join(UtilizationComment, Utilization.id == UtilizationComment.utilization_id)
        .join(
            UtilizationCommentReply,
            UtilizationComment.id == UtilizationCommentReply.utilization_comment_id,
        )
        .filter(
            Group.name.in_(org_names),
            Package.state == "active",
            Resource.state == "active",
        )
    )


def get_simple_utilization_comment_replies_query(org_list):
    org_names = [org['name'] for org in org_list]

    return (
        session.query(
            Group.name.label('group_name'),
            literal('utilization_comment_reply').label('feedback_type'),
            UtilizationCommentReply.approval.label('is_approved'),
        )
        .join(Package, Group.id == Package.owner_org)
        .join(Resource, Package.id == Resource.package_id)
        .join(Utilization, Resource.id == Utilization.resource_id)
        .join(UtilizationComment, Utilization.id == UtilizationComment.utilization_id)
        .join(
            UtilizationCommentReply,
            UtilizationComment.id == UtilizationCommentReply.utilization_comment_id,
        )
        .filter(
            Group.name.in_(org_names),
            Package.state == "active",
            Resource.state == "active",
        )
    )


def approve_utilization_comment_replies(reply_id_list, approval_user_id):
    approved_parent_reply_ids = [
        reply_id
        for reply_id, parent_approved in (
            session.query(
                UtilizationCommentReply.id,
                UtilizationComment.approval,
            )
            .join(
                UtilizationComment,
                UtilizationComment.id == UtilizationCommentReply.utilization_comment_id,
            )
            .filter(UtilizationCommentReply.id.in_(reply_id_list))
            .all()
        )
        if parent_approved
    ]

    if not approved_parent_reply_ids:
        return 0

    session.bulk_update_mappings(
        UtilizationCommentReply,
        [
            {
                'id': reply_id,
                'approval': True,
                'approved': datetime.now(),
                'approval_user_id': approval_user_id,
            }
            for reply_id in approved_parent_reply_ids
        ],
    )

    return len(approved_parent_reply_ids)


def delete_utilization_comment_replies(reply_id_list):
    session.query(UtilizationCommentReply).filter(
        UtilizationCommentReply.id.in_(reply_id_list)
    ).delete(synchronize_session='fetch')
