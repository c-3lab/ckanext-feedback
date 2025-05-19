import logging
import uuid
from datetime import datetime

from ckan.model import Resource
from sqlalchemy import extract, func

from ckanext.feedback.models.likes import ResourceLike, ResourceLikeMonthly
from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


def increment_resource_like_count(resource_id):
    resource_like = (
        session.query(ResourceLike)
        .filter(ResourceLike.resource_id == resource_id)
        .first()
    )

    if resource_like is None:
        resource_like = ResourceLike(
            id=str(uuid.uuid4()),
            resource_id=resource_id,
            like_count=1,
            created=datetime.now(),
            updated=datetime.now(),
        )
        session.add(resource_like)
    else:
        resource_like.like_count = resource_like.like_count + 1
        resource_like.updated = datetime.now()


def decrement_resource_like_count(resource_id):
    resource_like = (
        session.query(ResourceLike)
        .filter(ResourceLike.resource_id == resource_id)
        .first()
    )

    if resource_like is not None:
        resource_like.like_count = resource_like.like_count - 1
        resource_like.updated = datetime.now()


def increment_resource_like_count_monthly(resource_id):
    current_year = datetime.now().year
    current_month = datetime.now().month

    resource_like_monthly = (
        session.query(ResourceLikeMonthly)
        .filter(
            ResourceLikeMonthly.resource_id == resource_id,
            extract('year', ResourceLikeMonthly.created) == current_year,
            extract('month', ResourceLikeMonthly.created) == current_month,
        )
        .first()
    )

    if resource_like_monthly is None:
        resource_like_monthly = ResourceLikeMonthly(
            id=str(uuid.uuid4()),
            resource_id=resource_id,
            like_count=1,
            created=datetime.now(),
            updated=datetime.now(),
        )
        session.add(resource_like_monthly)
    else:
        resource_like_monthly.like_count = resource_like_monthly.like_count + 1
        resource_like_monthly.updated = datetime.now()


def decrement_resource_like_count_monthly(resource_id):
    current_year = datetime.now().year
    current_month = datetime.now().month

    resource_like_monthly = (
        session.query(ResourceLikeMonthly)
        .filter(
            ResourceLikeMonthly.resource_id == resource_id,
            extract('year', ResourceLikeMonthly.created) == current_year,
            extract('month', ResourceLikeMonthly.created) == current_month,
        )
        .first()
    )

    if resource_like_monthly is not None:
        resource_like_monthly.like_count = resource_like_monthly.like_count - 1
        resource_like_monthly.updated = datetime.now()


def get_resource_like_count(resource_id):
    count = (
        session.query(ResourceLike.like_count)
        .filter(ResourceLike.resource_id == resource_id)
        .first()
    )

    like_count = count[0] if count is not None else 0

    return like_count


def get_package_like_count(package_id):
    count = (
        session.query(func.sum(ResourceLike.like_count))
        .join(Resource)
        .filter(
            Resource.package_id == package_id,
            Resource.state == "active",
        )
        .scalar()
    )
    return count or 0


def get_resource_like_count_monthly(resource_id, period):
    count = (
        session.query(ResourceLikeMonthly.like_count)
        .filter(
            ResourceLikeMonthly.resource_id == resource_id,
            func.date_trunc('month', ResourceLikeMonthly.created) == func.date(period),
        )
        .scalar()
    )

    return count or 0
