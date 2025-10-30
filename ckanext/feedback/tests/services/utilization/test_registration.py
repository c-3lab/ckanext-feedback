import pytest

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization
from ckanext.feedback.services.utilization.registration import create_utilization


def get_utilization(resource_id):
    return (
        session.query(
            Utilization.title,
            Utilization.url,
            Utilization.description,
        )
        .filter(Utilization.resource_id == resource_id)
        .first()
    )


@pytest.mark.db_test
class TestUtilizationDetailsService:
    def test_create_utilization(self, resource):
        title = 'test title'
        url = 'test url'
        description = 'test description'

        assert get_utilization(resource['id']) is None

        create_utilization(resource['id'], title, url, description)
        session.commit()

        result = get_utilization(resource['id'])

        assert result.title == title
        assert result.url == url
        assert result.description == description
