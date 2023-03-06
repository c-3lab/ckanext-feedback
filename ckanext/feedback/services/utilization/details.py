import uuid
from datetime import datetime

from ckan.model.package import Package
from ckan.model.resource import Resource

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
    UtilizationSummary,
)
from ckanext.feedback.models.issue import IssueResolution, IssueResolutionSummary

# Get details from the Utilization record
def get_utilization(utilization_id):
    row = (
        session.query(
            Utilization.title,
            Utilization.description,
            Utilization.approval,
            Resource.name.label('resource_name'),
            Resource.id.label('resource_id'),
            Package.name.label('package_name'),
        )
        .join(Resource, Resource.id == Utilization.resource_id)
        .join(Package, Package.id == Resource.package_id)
        .filter(Utilization.id == utilization_id)
        .first()
    )
    return row


# Approve currently displayed utilization
def approve_utilization(utilization_id, approval_user_id):
    utilization = session.query(Utilization).get(utilization_id)
    utilization.approval = True
    utilization.approved = datetime.now()
    utilization.approval_user_id = approval_user_id


# Get comments related to the Utilization record
def get_utilization_comments(utilization_id, approval=None):
    query = (
        session.query(UtilizationComment)
        .filter(UtilizationComment.utilization_id == utilization_id)
        .order_by(UtilizationComment.created.desc())
    )
    if approval:
        query = query.filter(UtilizationComment.approval == approval)

    return query.all()


# Create comment for currently displayed utilization
def create_utilization_comment(utilization_id, comment_type, comment_content):
    comment = UtilizationComment(
        id=str(uuid.uuid4()),
        utilization_id=utilization_id,
        category=comment_type,
        content=comment_content,
        created=datetime.now(),
    )
    session.add(comment)
    session.flush()
    increment_utilization_summary(comment.utilization.resource_id)


# Approve selected utilization comment
def approve_utilization_comment(comment_id, approval_user_id):
    comment = session.query(UtilizationComment).get(comment_id)
    comment.approval = True
    comment.approved = datetime.now()
    comment.approval_user_id = approval_user_id


# Get comment category enum names and values
def get_utilization_comment_categories():
    return UtilizationCommentCategory


# Get issues resolved related to the Utilization record
def get_issue_resolution(utilization_id):
    rows = (
        session.query(
            IssueResolution.description,
            IssueResolution.created
        )
        .filter(IssueResolution.utilization_id == utilization_id)
        .order_by(IssueResolution.created.desc())
        .all()
    )
    return rows


# Create issue resolution
def create_issue_resolution(utilization_id, issue_resolution_description, creator):
    try:
        session.execute(
            insert(IssueResolution).values(
                id=str(uuid.uuid4()),
                utilization_id=utilization_id,
                description=issue_resolution_description,
                created=datetime.now(),
                creator_user_id=creator,
            )
        )
        increment_issue_resolution_summary(utilization_id)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


# Increment utilization summary comment count
def increment_utilization_summary(resource_id):
    summary = (
        session.query(UtilizationSummary)
        .filter(UtilizationSummary.resource_id == resource_id)
        .first()
    )
    summary.comment = summary.comment + 1
    summary.updated = datetime.now()

# Increment issue resolution count
def increment_issue_resolution_summary(utilization_id):
    try:
        if (session.query(IssueResolutionSummary).filter(IssueResolutionSummary.utilization_id == utilization_id).count() > 0):
            session.execute(
                update(IssueResolutionSummary)
                .where(IssueResolutionSummary.utilization_id == utilization_id)
                .values(
                    issue_resolution=len(get_issue_resolution(utilization_id)),
                    updated=datetime.now(),
                )
            )
        else:
            session.execute(
                insert(IssueResolutionSummary).values(
                    id=str(uuid.uuid4()),
                    utilization_id=utilization_id,
                    issue_resolution=1,
                    created=datetime.now(),
                    updated=datetime.now(),
                )
            )
    except Exception as e:
        session.rollback()
        raise e
