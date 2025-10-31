from datetime import datetime

import pytest

from ckanext.feedback.models.likes import ResourceLike, ResourceLikeMonthly
from ckanext.feedback.models.session import session
from ckanext.feedback.services.resource.likes import (
    decrement_resource_like_count,
    decrement_resource_like_count_monthly,
    get_package_like_count,
    get_resource_like_count,
    get_resource_like_count_monthly,
    increment_resource_like_count,
    increment_resource_like_count_monthly,
)


def get_resource_like(resource_id):
    return (
        session.query(ResourceLike)
        .filter(ResourceLike.resource_id == resource_id)
        .first()
    )


def get_resource_like_monthly(resource_id):
    return (
        session.query(ResourceLikeMonthly)
        .filter(ResourceLikeMonthly.resource_id == resource_id)
        .first()
    )


@pytest.mark.db_test
class TestLikes:
    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_increment_resource_like_count(self, resource):
        increment_resource_like_count(resource['id'])
        session.commit()
        resource_like = get_resource_like(resource['id'])

        assert resource_like.like_count == 1
        assert resource_like.created == datetime(2024, 1, 1, 15, 0, 0)
        assert resource_like.updated == datetime(2024, 1, 1, 15, 0, 0)

        increment_resource_like_count(resource['id'])
        session.commit()
        session.expire_all()
        resource_like = get_resource_like(resource['id'])

        assert resource_like.like_count == 2
        assert resource_like.created == datetime(2024, 1, 1, 15, 0, 0)
        assert resource_like.updated == datetime(2024, 1, 1, 15, 0, 0)

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_decrement_resource_like_count(self, resource):
        decrement_resource_like_count(resource['id'])
        session.commit()
        resource_like = get_resource_like(resource['id'])

        assert resource_like is None

        increment_resource_like_count(resource['id'])
        session.commit()
        resource_like = get_resource_like(resource['id'])

        assert resource_like.like_count == 1
        assert resource_like.created == datetime(2024, 1, 1, 15, 0, 0)
        assert resource_like.updated == datetime(2024, 1, 1, 15, 0, 0)

        decrement_resource_like_count(resource['id'])
        session.commit()
        resource_like = get_resource_like(resource['id'])

        assert resource_like.like_count == 0
        assert resource_like.created == datetime(2024, 1, 1, 15, 0, 0)
        assert resource_like.updated == datetime(2024, 1, 1, 15, 0, 0)

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_increment_resource_like_count_monthly(self, resource):
        increment_resource_like_count_monthly(resource['id'])
        session.commit()
        resource_like_monthly = get_resource_like_monthly(resource['id'])

        assert resource_like_monthly.like_count == 1
        assert resource_like_monthly.created == datetime(2024, 1, 1, 15, 0, 0)
        assert resource_like_monthly.updated == datetime(2024, 1, 1, 15, 0, 0)

        increment_resource_like_count_monthly(resource['id'])
        session.commit()
        resource_like_monthly = get_resource_like_monthly(resource['id'])

        assert resource_like_monthly.like_count == 2
        assert resource_like_monthly.created == datetime(2024, 1, 1, 15, 0, 0)
        assert resource_like_monthly.updated == datetime(2024, 1, 1, 15, 0, 0)

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_decrement_resource_like_count_monthly(self, resource):
        decrement_resource_like_count_monthly(resource['id'])
        session.commit()
        resource_like_monthly = get_resource_like_monthly(resource['id'])

        assert resource_like_monthly is None

        increment_resource_like_count_monthly(resource['id'])
        session.commit()
        resource_like_monthly = get_resource_like_monthly(resource['id'])

        assert resource_like_monthly.like_count == 1
        assert resource_like_monthly.created == datetime(2024, 1, 1, 15, 0, 0)
        assert resource_like_monthly.updated == datetime(2024, 1, 1, 15, 0, 0)

        decrement_resource_like_count_monthly(resource['id'])
        session.commit()
        resource_like_monthly = get_resource_like_monthly(resource['id'])

        assert resource_like_monthly.like_count == 0
        assert resource_like_monthly.created == datetime(2024, 1, 1, 15, 0, 0)
        assert resource_like_monthly.updated == datetime(2024, 1, 1, 15, 0, 0)

    def test_get_resource_like_count(self, resource_like):
        assert (
            get_resource_like_count(resource_like.resource_id)
            == resource_like.like_count
        )

    def test_get_package_like_count(self, resource, resource_like):
        assert (
            get_package_like_count(resource['package_id']) == resource_like.like_count
        )

    def test_get_resource_like_count_monthly(self, resource_like_monthly):
        assert (
            get_resource_like_count_monthly(
                resource_like_monthly.resource_id, '2024-01-01'
            )
            == resource_like_monthly.like_count
        )
