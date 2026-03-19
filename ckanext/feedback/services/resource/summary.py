import logging
from datetime import datetime

from ckan.model.resource import Resource
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentSummary,
)
from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


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


def get_package_comments_bulk(package_ids):
    rows = (
        session.query(Resource.package_id, func.sum(ResourceCommentSummary.comment))
        .join(Resource, ResourceCommentSummary.resource_id == Resource.id)
        .filter(
            Resource.package_id.in_(package_ids),
            Resource.state == "active",
        )
        .group_by(Resource.package_id)
        .all()
    )
    return {str(r.package_id): r[1] or 0 for r in rows}


# Get comments of the target resource
def get_resource_comments(resource_id):
    count = (
        session.query(ResourceCommentSummary.comment)
        .filter(ResourceCommentSummary.resource_id == resource_id)
        .scalar()
    )
    return count or 0


# Get rating of the target get_package_issue_resolutions_bulk
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


def get_package_rating_bulk(package_ids):
    rows = (
        session.query(
            Resource.package_id,
            func.sum(
                ResourceCommentSummary.rating * ResourceCommentSummary.rating_comment
            ).label('total'),
            func.sum(ResourceCommentSummary.rating_comment).label('denom'),
        )
        .join(Resource, ResourceCommentSummary.resource_id == Resource.id)
        .filter(
            Resource.package_id.in_(package_ids),
            Resource.state == "active",
        )
        .group_by(Resource.package_id)
        .all()
    )
    result = {}
    for r in rows:
        pid = str(r.package_id)
        result[pid] = (r.total / r.denom) if r.denom and r.denom > 0 else 0
    return result


# Get rating of the target resource
def get_resource_rating(resource_id):
    rating = (
        session.query(ResourceCommentSummary.rating)
        .filter(ResourceCommentSummary.resource_id == resource_id)
        .scalar()
    )
    if rating is None or rating == 0:
        return 0
    return round(rating, 1)


# Create new resource summary
def create_resource_summary(resource_id):
    summary = insert(ResourceCommentSummary).values(
        resource_id=resource_id,
    )
    summary = summary.on_conflict_do_nothing(index_elements=['resource_id'])
    session.execute(summary)


# Recalculate approved ratings and comments related to the resource summary
def refresh_resource_summary(resource_id):
    now = datetime.now()

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

    insert_summary = insert(ResourceCommentSummary).values(
        resource_id=resource_id,
        rating=rating,
        comment=comment,
        rating_comment=rating_comment,
    )
    summary = insert_summary.on_conflict_do_update(
        index_elements=['resource_id'],
        set_={
            'rating': insert_summary.excluded.rating,
            'comment': insert_summary.excluded.comment,
            'rating_comment': insert_summary.excluded.rating_comment,
            'updated': now,
        },
    )
    session.execute(summary)
