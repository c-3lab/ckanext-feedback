from datetime import datetime

from ckan.lib.uploader import get_uploader
from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from ckan.types import PUploader
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentCategory,
    ResourceCommentReactions,
    ResourceCommentReply,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.types import ResourceCommentResponseStatus


# Get resource from the selected resource_id
def get_resource(resource_id):
    return (
        session.query(
            Resource,
            Package.id.label('organization_id'),
            Group.name.label('organization_name'),
        )
        .join(Package)
        .join(Group, Package.owner_org == Group.id)
        .filter(Resource.id == resource_id)
        .first()
    )


# Get a comment related to the dataset or resource
def get_resource_comment(
    comment_id: str,
    resource_id: str = None,
    approval: bool = None,
    attached_image_filename: str = None,
    owner_orgs=None,
):
    query = session.query(ResourceComment).filter(ResourceComment.id == comment_id)
    if resource_id is not None:
        query = query.filter(ResourceComment.resource_id == resource_id)
    if approval is not None:
        query = query.filter(ResourceComment.approval == approval)
    if attached_image_filename is not None:
        query = query.filter(
            ResourceComment.attached_image_filename == attached_image_filename
        )
    if owner_orgs is not None:
        query = (
            query.join(Resource).join(Package).filter(Package.owner_org.in_(owner_orgs))
        )

    return query.first()


# Get comments related to the dataset or resource
def get_resource_comments(
    resource_id=None, approval=None, owner_orgs=None, limit=None, offset=None
):
    query = (
        session.query(ResourceComment)
        .options(joinedload(ResourceComment.reactions))
        .order_by(ResourceComment.created.desc())
    )
    if resource_id is not None:
        query = query.filter(ResourceComment.resource_id == resource_id)
    if approval is not None:
        query = query.filter(ResourceComment.approval == approval)
    if owner_orgs is not None:
        query = (
            query.join(Resource).join(Package).filter(Package.owner_org.in_(owner_orgs))
        )

    results = query.limit(limit).offset(offset).all()
    if limit is not None or offset is not None:
        total_count = query.count()
        return results, total_count
    return results


# Get category enum names and values
def get_resource_comment_categories():
    return ResourceCommentCategory


# Create new comment
def create_resource_comment(
    resource_id, category, content, rating, attached_image_filename=None
):
    now = datetime.now()

    comment = ResourceComment(
        resource_id=resource_id,
        category=category,
        content=content,
        rating=rating,
        attached_image_filename=attached_image_filename,
        created=now,
    )
    session.add(comment)
    session.flush()

    insert_reactions = insert(ResourceCommentReactions).values(
        resource_comment_id=comment.id,
        response_status=ResourceCommentResponseStatus.STATUS_NONE,
        created=now,
    )
    reactions = insert_reactions.on_conflict_do_update(
        index_elements=['resource_comment_id'],
        set_={
            'response_status': ResourceCommentResponseStatus.STATUS_NONE,
            'admin_liked': False,
            'created': now,
            'updated': None,
            'updater_user_id': None,
        },
    )
    session.execute(reactions)


# Approve selected resource comment
def approve_resource_comment(resource_comment_id, approval_user_id):
    comment = session.query(ResourceComment).get(resource_comment_id)
    comment.approval = True
    comment.approved = datetime.now()
    comment.approval_user_id = approval_user_id


# Get reply for target comment
def get_comment_reply(resource_comment_id):
    return (
        session.query(ResourceCommentReply)
        .filter(ResourceCommentReply.resource_comment_id == resource_comment_id)
        .first()
    )


# Create new reply
def create_reply(resource_comment_id, content, creator_user_id):
    reply = ResourceCommentReply(
        resource_comment_id=resource_comment_id,
        content=content,
        creator_user_id=creator_user_id,
    )
    session.add(reply)


def get_resource_comment_reactions(resource_comment_id):
    result = (
        session.query(ResourceCommentReactions)
        .filter(ResourceCommentReactions.resource_comment_id == resource_comment_id)
        .first()
    )

    return result


def create_resource_comment_reactions(
    resource_comment_id,
    response_status,
    admin_liked,
    updater_user_id,
):
    now = datetime.now()

    insert_reactions = insert(ResourceCommentReactions).values(
        resource_comment_id=resource_comment_id,
        response_status=response_status,
        admin_liked=admin_liked,
        created=now,
        updated=now,
        updater_user_id=updater_user_id,
    )
    reactions = insert_reactions.on_conflict_do_update(
        index_elements=['resource_comment_id'],
        set_={
            'response_status': response_status,
            'admin_liked': admin_liked,
            'updated': now,
            'updater_user_id': updater_user_id,
        },
    )
    session.execute(reactions)


def update_resource_comment_reactions(
    reactions,
    response_status,
    admin_liked,
    updater_user_id,
):
    reactions.response_status = response_status
    reactions.admin_liked = admin_liked
    reactions.updated = datetime.now()
    reactions.updater_user_id = updater_user_id
    return


# Get path for attached image
def get_attached_image_path(attached_image_filename: str) -> str:
    upload_to = get_upload_destination()
    uploader: PUploader = get_uploader(upload_to, attached_image_filename)
    return uploader.old_filepath


# Get directory name to save attached image
def get_upload_destination() -> str:
    return "feedback_resouce_comment"


def get_comment_attached_image_files():
    image_files = (
        session.query(ResourceComment.attached_image_filename)
        .filter(ResourceComment.attached_image_filename.isnot(None))
        .all()
    )

    return [filename for (filename,) in image_files]
