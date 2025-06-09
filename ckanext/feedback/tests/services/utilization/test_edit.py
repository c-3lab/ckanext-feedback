import uuid

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
from ckanext.feedback.services.utilization.edit import (
    delete_utilization,
    get_resource_details,
    get_utilization_details,
    update_utilization,
)


def get_registered_utilization(id):
    return session.query(Utilization).filter(Utilization.id == id).first()


def register_utilization(id, resource_id, title, url, description, approval):
    utilization = Utilization(
        id=id,
        resource_id=resource_id,
        title=title,
        url=url,
        description=description,
        approval=approval,
    )
    session.add(utilization)


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

    def test_get_utilization_details(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(id, resource['id'], title, url, description, False)

        result = get_utilization_details(id)
        utilization = get_registered_utilization(id)
        assert result == utilization

    def test_get_resource_details(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        result = get_resource_details(resource['id'])

        assert result.resource_name == resource['name']
        assert result.resource_id == resource['id']
        assert result.package_title == dataset['title']
        assert result.package_name == dataset['name']

    def test_update_utilization(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(id, resource['id'], title, url, description, False)

        updated_title = 'test updated title'
        updated_url = 'test updated url'
        updated_description = 'test updated description'

        update_utilization(id, updated_title, updated_url, updated_description)

        utilization = get_registered_utilization(id)

        assert utilization.title == updated_title
        assert utilization.url == updated_url
        assert utilization.description == updated_description

    def test_delete_utilization(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(id, resource['id'], title, url, description, False)

        assert get_registered_utilization(id).id == id

        delete_utilization(id)

        assert get_registered_utilization(id) is None
