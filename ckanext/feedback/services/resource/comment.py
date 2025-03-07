from datetime import datetime
from urllib.parse import urljoin

from ckan.common import config
from ckan.lib.uploader import get_uploader
from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from ckan.types import PUploader
from flask import request

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentCategory,
    ResourceCommentReply,
)
from ckanext.feedback.models.session import session


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


# Get comments related to the dataset or resource
def get_resource_comments(
    resource_id=None, approval=None, owner_orgs=None, limit=None, offset=None
):
    query = session.query(ResourceComment).order_by(ResourceComment.created.desc())
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
    comment = ResourceComment(
        resource_id=resource_id,
        category=category,
        content=content,
        rating=rating,
        attached_image_filename=attached_image_filename,
    )
    session.add(comment)


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


# Get cookie
def get_cookie(resource_id):
    return request.cookies.get(resource_id)


# Get url for attached image
def get_attached_image_url(attached_image_filename: str) -> str:
    site_url = config.get('ckan.site_url', '')
    upload_to = get_upload_destination()
    uploader: PUploader = get_uploader(upload_to, attached_image_filename)
    return urljoin(site_url, f'uploads/{upload_to}/{uploader.old_filename}')


# Get path for attached image
def get_attached_image_path(attached_image_filename: str) -> str:
    upload_to = get_upload_destination()
    uploader: PUploader = get_uploader(upload_to, attached_image_filename)
    return uploader.old_filepath


# Get directory name to save attached image
def get_upload_destination() -> str:
    return "feedback_resouce_comment"
