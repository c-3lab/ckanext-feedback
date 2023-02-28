import uuid
from datetime import datetime

from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import insert, update
from sqlalchemy.orm import Session

from ckanext.feedback.models.utilization import (
    Utilization,
    Utilization_comment_category,
    UtilizationComment,
    UtilizationSummary
)

session = Session()


# Get details from the Utilization record
def get_utilization_details(utilization_id):
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
        .one()
    )
    return row


# Get comments related to the Utilization record
def get_utilization_comments(utilization_id):
    rows = (
        session.query(
            UtilizationComment.id,
            UtilizationComment.category,
            UtilizationComment.content,
            UtilizationComment.created,
            UtilizationComment.approval,
        )
        .filter(UtilizationComment.utilization_id == utilization_id)
        .order_by(UtilizationComment.created.desc())
        .all()
    )

    return rows


# Get approved comments related to the Utilization record
def get_approved_utilization_comments(utilization_id):
    rows = (
        session.query(
            UtilizationComment.id,
            UtilizationComment.category,
            UtilizationComment.content,
            UtilizationComment.created,
            UtilizationComment.approval,
        )
        .filter(
            UtilizationComment.utilization_id == utilization_id,
            UtilizationComment.approval == 'true',
        )
        .order_by(UtilizationComment.created.desc())
        .all()
    )

    return rows


# Get category enum names and values
def get_categories():
    # rows = Utilization_comment_category

    return Utilization_comment_category


# Submit comment
def submit_comment(utilization_id, comment_type, comment_content):
    if comment_type and comment_content:
        try:
            session.execute(
                insert(UtilizationComment).values(
                    id=str(uuid.uuid4()),
                    utilization_id=utilization_id,
                    category=comment_type,
                    content=comment_content,
                    created=datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                    approval=False,
                    approved=None,
                    approval_user_id=None,
                )
            )
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


# Submit comment approval
def submit_approval(comment_id, approval_user):
    try:
        session.execute(
            update(UtilizationComment)
            .where(UtilizationComment.id == comment_id)
            .values(
                approval=True,
                approved=datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                approval_user_id=approval_user,
            )
        )
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


# Approve currently displayed utilization
def approve_utilization(utilization_id, approval_user):
    try:
        session.execute(
            update(Utilization)
            .where(Utilization.id == utilization_id)
            .values(
                approval=True,
                approved=datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                approval_user_id=approval_user,
            )
        )
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


# Update utilization summary comment count
def update_utilization_summary(resource_id):
    count = (
        session.query(UtilizationSummary.comment)
        .filter(UtilizationSummary.resource_id == resource_id)
        .first()
    )
    try:
        session.execute(
            update(UtilizationSummary)
            .where(UtilizationSummary.resource_id == resource_id)
            .values(
                comment=count.comment + 1,
                updated=datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
            )
        )
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
