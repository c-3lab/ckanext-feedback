import pytest
from ckan import model
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.services.resource.likes import (
    create_resource_like,
    decrement_resource_like_count,
    get_all_resource_ids,
    get_resource_like_count,
    increment_resource_like_count,
)


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestLikes:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = model.meta.engine
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_all_resource_ids(self):
        organization = factories.Organization()
        package = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=package['id'])

        create_resource_like(resource['id'])
        session.commit()

        assert get_all_resource_ids()

    def test_create_resource_like(self):
        pass

    def test_increment_resource_like_count(self):
        pass

    def test_decrement_resource_like_count(self):
        pass

    def test_get_resource_like_count_with_increment(self):
        organization = factories.Organization()
        package = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=package['id'])

        create_resource_like(resource['id'])
        increment_resource_like_count(resource['id'])
        session.commit()

        assert get_resource_like_count(resource['id']) == 1

    def test_get_resource_like_count_with_decrement(self):
        organization = factories.Organization()
        package = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=package['id'])

        create_resource_like(resource['id'], 1)
        decrement_resource_like_count(resource['id'])
        session.commit()

        assert get_resource_like_count(resource['id']) == 0
