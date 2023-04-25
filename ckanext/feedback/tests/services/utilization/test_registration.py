import ckan.tests.factories as factories
import pytest
from ckan import model

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization
from ckanext.feedback.services.utilization.registration import (
    create_utilization,
    get_resource,
)


def get_utilization(resource_id):
    return (
        session.query(
            Utilization.title,
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
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_resource(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        result = get_resource(resource['id'])

        assert result.id == resource['id']
        assert result.package_id == resource['package_id']
        assert result.name == resource['name']
        assert result.description == resource['description']
        assert result.format == resource['format']
        assert result.url == resource['url']

    def test_create_utilization(self):
        resource = factories.Resource()

        title = 'test title'
        description = 'test description'

        assert get_utilization(resource['id']) is None

        create_utilization(resource['id'], title, description)

        result = get_utilization(resource['id'])

        assert result.title == title
        assert result.description == description
