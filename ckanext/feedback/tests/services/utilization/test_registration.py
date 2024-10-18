import ckan.tests.factories as factories
import pytest
from ckan import model

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
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


engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestUtilizationDetailsService:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_create_utilization(self):
        resource = factories.Resource()

        title = 'test title'
        url = 'test url'
        description = 'test description'

        assert get_utilization(resource['id']) is None

        create_utilization(resource['id'], title, url, description)

        result = get_utilization(resource['id'])

        assert result.title == title
        assert result.url == url
        assert result.description == description
