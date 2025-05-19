from datetime import datetime

from ckan.model.resource import Resource
from sqlalchemy import func

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentSummary,
)
from ckanext.feedback.models.session import session


# Get comments of the target package
def get_package_comments(package_id):
    count = (
        session.query(func.sum(ResourceCommentSummary.comment))
        .join(Resource)
        .filter(
            Resource.package_id == package_id,
            Resource.state == "active",
        )
        .scalar()
    )
    return count or 0


# Get comments of the target resource
def get_resource_comments(resource_id):
    count = (
        session.query(ResourceCommentSummary.comment)
        .filter(ResourceCommentSummary.resource_id == resource_id)
        .scalar()
    )
    return count or 0


# Get rating of the target package
def get_package_rating(package_id):
    row = (
        session.query(
            func.sum(
                ResourceCommentSummary.rating * ResourceCommentSummary.rating_comment
            ).label('total_rating'),
            func.sum(ResourceCommentSummary.rating_comment).label('rating_comment'),
        )
        .join(Resource)
        .filter(
            Resource.package_id == package_id,
            Resource.state == "active",
        )
        .first()
    )
    if row and row.rating_comment and row.rating_comment > 0:
        return row.total_rating / row.rating_comment
    else:
        return 0


# Get rating of the target resource
def get_resource_rating(resource_id):
    rating = (
        session.query(ResourceCommentSummary.rating)
        .filter(ResourceCommentSummary.resource_id == resource_id)
        .scalar()
    )
    return rating or 0


# Create new resource summary
def create_resource_summary(resource_id):
    summary = (
        session.query(ResourceCommentSummary)
        .filter(ResourceCommentSummary.resource_id == resource_id)
        .first()
    )
    if summary is None:
        summary = ResourceCommentSummary(
            resource_id=resource_id,
        )
        session.add(summary)


# Recalculate approved ratings and comments related to the resource summary
def refresh_resource_summary(resource_id):
    total_rating = (
        session.query(
            func.sum(ResourceComment.rating),
        )
        .filter(
            ResourceComment.resource_id == resource_id,
            ResourceComment.approval,
            ResourceComment.rating.isnot(None),
        )
        .scalar()
    )
    if total_rating is None:
        total_rating = 0
    total_comment = (
        session.query(ResourceComment)
        .filter(
            ResourceComment.resource_id == resource_id,
            ResourceComment.approval,
            ResourceComment.rating.isnot(None),
        )
        .count()
    )
    if total_comment > 0:
        rating = total_rating / total_comment
        rating_comment = total_comment
    else:
        rating = 0
        rating_comment = 0

    comment = (
        session.query(ResourceComment)
        .filter(
            ResourceComment.resource_id == resource_id,
            ResourceComment.approval,
            ResourceComment.content.isnot(None),
        )
        .count()
    )

    summary = (
        session.query(ResourceCommentSummary)
        .filter(ResourceCommentSummary.resource_id == resource_id)
        .first()
    )
    if summary is None:
        summary = ResourceCommentSummary(
            resource_id=resource_id,
            rating=rating,
            comment=comment,
            rating_comment=rating_comment,
        )
        session.add(summary)
    else:
        summary.rating = rating
        summary.comment = comment
        summary.rating_comment = rating_comment
        summary.updated = datetime.now()
