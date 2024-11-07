import logging
from datetime import datetime

from ckan.model import Resource
from sqlalchemy import func

from ckanext.feedback.models.likes import ResourceLike
from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


def get_all_resource_ids():
    resource_ids = session.query(ResourceLike.resource_id).with_for_update().all()

    resource_id_list = [r.resource_id for r in resource_ids]

    return resource_id_list


def create_resource_like(
    resource_id, like_count=0, created=datetime.now(), updated=datetime.now()
):
    resource_like = ResourceLike(
        resource_id=resource_id,
        like_count=like_count,
        created=created,
        updated=updated,
    )
    session.add(resource_like)


def increment_resource_like_count(resource_id):
    session.query(ResourceLike).filter(ResourceLike.resource_id == resource_id).update(
        {
            ResourceLike.like_count: ResourceLike.like_count + 1,
            ResourceLike.updated: datetime.now(),
        }
    )


def decrement_resource_like_count(resource_id):
    session.query(ResourceLike).filter(ResourceLike.resource_id == resource_id).update(
        {
            ResourceLike.like_count: ResourceLike.like_count - 1,
            ResourceLike.updated: datetime.now(),
        }
    )


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
        .filter(Resource.package_id == package_id)
        .scalar()
    )
    return count or 0
