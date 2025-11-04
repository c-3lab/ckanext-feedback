from datetime import datetime

import ckan.model as model
from ckan.common import current_user
from ckan.lib.uploader import get_uploader
from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from ckan.types import PUploader

from ckanext.feedback.models.issue import IssueResolution
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
    UtilizationCommentMoralCheckLog,
    UtilizationCommentReply,
)
from ckanext.feedback.services.common.check import has_organization_admin_role


# Get details from the Utilization record
def get_utilization(utilization_id):
    return (
        session.query(
            Utilization.title,
            Utilization.url,
            Utilization.description,
            Utilization.comment,
            Utilization.approval,
            Resource.name.label('resource_name'),
            Resource.id.label('resource_id'),
            Package.id.label('package_id'),
            Package.title.label('package_title'),
            Package.name.label('package_name'),
            Package.owner_org,
        )
        .join(Resource, Utilization.resource)
        .join(Package)
        .filter(
            Utilization.id == utilization_id,
            Package.state == 'active',
        )
        .first()
    )


# Approve currently displayed utilization
def approve_utilization(utilization_id, approval_user_id):
    utilization = session.query(Utilization).get(utilization_id)
    utilization.approval = True
    utilization.approved = datetime.now()
    utilization.approval_user_id = approval_user_id


# Get a comment related to the Utilization record
def get_utilization_comment(
    comment_id: str,
    utilization_id: str = None,
    approval: bool = None,
    attached_image_filename: str = None,
    owner_orgs=None,
):
    query = session.query(UtilizationComment).filter(
        UtilizationComment.id == comment_id
    )
    if utilization_id is not None:
        query = query.filter(UtilizationComment.utilization_id == utilization_id)
    if approval is not None:
        query = query.filter(UtilizationComment.approval == approval)
    if attached_image_filename is not None:
        query = query.filter(
            UtilizationComment.attached_image_filename == attached_image_filename
        )
    if owner_orgs is not None:
        query = (
            query.join(Utilization)
            .join(Resource)
            .join(Package)
            .filter(Package.owner_org.in_(owner_orgs))
        )

    return query.first()


# Get comments related to the Utilization record
def get_utilization_comments(
    utilization_id=None, approval=None, owner_orgs=None, limit=None, offset=None
):
    query = session.query(UtilizationComment).order_by(
        UtilizationComment.created.desc()
    )
    if utilization_id is not None:
        query = query.filter(UtilizationComment.utilization_id == utilization_id)
    if approval is not None:
        query = query.filter(UtilizationComment.approval == approval)
    if owner_orgs is not None:
        query = (
            query.join(Utilization)
            .join(Resource)
            .join(Package)
            .filter(Package.owner_org.in_(owner_orgs))
        )

    results = query.limit(limit).offset(offset).all()
    if limit is not None or offset is not None:
        total_count = query.count()
        return results, total_count
    return results


# Get replies for a utilization comment
def get_utilization_comment_replies(utilization_comment_id, approval=None):
    query = (
        session.query(UtilizationCommentReply)
        .filter(
            UtilizationCommentReply.utilization_comment_id == utilization_comment_id
        )
        .order_by(UtilizationCommentReply.created.asc())
    )
    if approval is not None:
        query = query.filter(UtilizationCommentReply.approval == approval)
    return query.all()


# Create comment for currently displayed utilization
def create_utilization_comment(
    utilization_id, category, content, attached_image_filename=None
):
    comment = UtilizationComment(
        utilization_id=utilization_id,
        category=category,
        content=content,
        attached_image_filename=attached_image_filename,
    )
    session.add(comment)


def create_utilization_comment_reply(
    utilization_comment_id, content, creator_user_id, attached_image_filename=None
):
    reply = UtilizationCommentReply(
        utilization_comment_id=utilization_comment_id,
        content=content,
        creator_user_id=creator_user_id,
        attached_image_filename=attached_image_filename,
    )
    session.add(reply)


# Approve selected utilization comment
def approve_utilization_comment(comment_id, approval_user_id):
    comment = session.query(UtilizationComment).get(comment_id)
    comment.approval = True
    comment.approved = datetime.now()
    comment.approval_user_id = approval_user_id


# Approve a reply for a utilization comment
def approve_utilization_comment_reply(reply_id: str, approval_user_id: str):
    reply = session.query(UtilizationCommentReply).get(reply_id)
    if reply is None:
        raise ValueError('Reply not found')

    parent_comment = session.query(UtilizationComment).get(reply.utilization_comment_id)
    if parent_comment is None:
        raise ValueError('Parent comment not found')

    if not parent_comment.approval:
        # Keep parity with resource side: cannot approve reply before parent
        raise PermissionError('Cannot approve reply before parent comment is approved')

    reply.approval = True
    reply.approved = datetime.now()
    reply.approval_user_id = approval_user_id


# Get comment category enum names and values
def get_utilization_comment_categories():
    return UtilizationCommentCategory


# Get issues resolved related to the Utilization record
def get_issue_resolutions(utilization_id):
    return (
        session.query(IssueResolution)
        .filter(IssueResolution.utilization_id == utilization_id)
        .order_by(IssueResolution.created.desc())
        .all()
    )


# Create issue resolution
def create_issue_resolution(utilization_id, description, creator_user_id):
    issue_resolution = IssueResolution(
        utilization_id=utilization_id,
        description=description,
        creator_user_id=creator_user_id,
    )
    session.add(issue_resolution)


# Recalculate total approved utilization comments
def refresh_utilization_comments(utilization_id):
    count = (
        session.query(UtilizationComment)
        .filter(
            UtilizationComment.utilization_id == utilization_id,
            UtilizationComment.approval,
        )
        .count()
    )
    utilization = session.query(Utilization).get(utilization_id)
    utilization.comment = count
    utilization.updated = datetime.now()


# Get path for attached image
def get_attached_image_path(attached_image_filename: str) -> str:
    upload_to = get_upload_destination()
    uploader: PUploader = get_uploader(upload_to, attached_image_filename)
    return uploader.old_filepath


# Get directory name to save attached image
def get_upload_destination() -> str:
    return "feedback_utilization_comment"


def get_comment_attached_image_files():
    image_files = (
        session.query(UtilizationComment.attached_image_filename)
        .filter(UtilizationComment.attached_image_filename.isnot(None))
        .all()
    )

    return [filename for (filename,) in image_files]


def get_utilization_comment_replies_for_display(utilization_comment_id, owner_org_id):
    approval = (
        None
        if (
            isinstance(current_user, model.User)
            and (current_user.sysadmin or has_organization_admin_role(owner_org_id))
        )
        else True
    )
    return get_utilization_comment_replies(utilization_comment_id, approval=approval)


def create_utilization_comment_moral_check_log(
    utilization_id, action, input_comment, suggested_comment, output_comment
):
    now = datetime.now()

    moral_check_log = UtilizationCommentMoralCheckLog(
        utilization_id=utilization_id,
        action=action,
        input_comment=input_comment,
        suggested_comment=suggested_comment,
        output_comment=output_comment,
        timestamp=now,
    )
    session.add(moral_check_log)


def get_resource_by_utilization_id(utilization_id):
    return (
        session.query(
            Resource,
            Package.id.label('organization_id'),
            Group.name.label('organization_name'),
        )
        .join(Utilization, Utilization.resource_id == Resource.id)
        .join(Package, Resource.package_id == Package.id)
        .join(Group, Package.owner_org == Group.id)
        .filter(Utilization.id == utilization_id)
        .first()
    )


def get_utilization_comment_moral_check_logs():
    return session.query(UtilizationCommentMoralCheckLog).all()
