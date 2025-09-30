from datetime import datetime

from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import literal

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentReply,
)
from ckanext.feedback.models.session import session


def get_resource_comment_replies_query(org_list):
    org_names = [org['name'] for org in org_list]

    return (
        session.query(
            Group.name.label('group_name'),
            Package.name.label('package_name'),
            Package.title.label('package_title'),
            Package.owner_org.label('owner_org'),
            Resource.id.label('resource_id'),
            Resource.name.label('resource_name'),
            literal(None).label('utilization_id'),
            literal('resource_comment_reply').label('feedback_type'),
            ResourceCommentReply.id.label('comment_id'),
            ResourceCommentReply.content.label('content'),
            ResourceCommentReply.created.label('created'),
            ResourceCommentReply.approval.label('is_approved'),
        )
        .select_from(Package)
        .join(Group, Package.owner_org == Group.id)
        .join(Resource, Package.id == Resource.package_id)
        .join(ResourceComment, Resource.id == ResourceComment.resource_id)
        .join(
            ResourceCommentReply,
            ResourceComment.id == ResourceCommentReply.resource_comment_id,
        )
        .filter(
            Group.name.in_(org_names),
            Package.state == "active",
            Resource.state == "active",
        )
    )


def get_simple_resource_comment_replies_query(org_list):
    org_names = [org['name'] for org in org_list]

    return (
        session.query(
            Group.name.label('group_name'),
            literal('resource_comment_reply').label('feedback_type'),
            ResourceCommentReply.approval.label('is_approved'),
        )
        .join(Package, Group.id == Package.owner_org)
        .join(Resource, Package.id == Resource.package_id)
        .join(ResourceComment, Resource.id == ResourceComment.resource_id)
        .join(
            ResourceCommentReply,
            ResourceComment.id == ResourceCommentReply.resource_comment_id,
        )
        .filter(
            Group.name.in_(org_names),
            Package.state == "active",
            Resource.state == "active",
        )
    )


def approve_resource_comment_replies(reply_id_list, approval_user_id):
    approved_parent_reply_ids = [
        reply_id
        for reply_id, parent_approved in (
            session.query(
                ResourceCommentReply.id,
                ResourceComment.approval,
            )
            .join(
                ResourceComment,
                ResourceComment.id == ResourceCommentReply.resource_comment_id,
            )
            .filter(ResourceCommentReply.id.in_(reply_id_list))
            .all()
        )
        if parent_approved
    ]

    if not approved_parent_reply_ids:
        return 0

    session.bulk_update_mappings(
        ResourceCommentReply,
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


def delete_resource_comment_replies(reply_id_list):
    session.query(ResourceCommentReply).filter(
        ResourceCommentReply.id.in_(reply_id_list)
    ).delete(synchronize_session='fetch')
