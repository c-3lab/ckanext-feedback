from datetime import datetime

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
    decrement_resource_like_count,
    decrement_resource_like_count_monthly,
    get_package_like_count,
    get_resource_like_count,
    get_resource_like_count_monthly,
    increment_resource_like_count,
    increment_resource_like_count_monthly,
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

    def test_increment_decrement_resource_like_count(self):
        organization = factories.Organization()
        package = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=package['id'])

        assert get_resource_like_count(resource['id']) == 0
        assert get_package_like_count(package['id']) == 0

        increment_resource_like_count(resource['id'])
        session.commit()

        assert get_resource_like_count(resource['id']) == 1
        assert get_package_like_count(package['id']) == 1

        increment_resource_like_count(resource['id'])
        session.commit()

        assert get_resource_like_count(resource['id']) == 2
        assert get_package_like_count(package['id']) == 2

        decrement_resource_like_count(resource['id'])
        session.commit()

        assert get_resource_like_count(resource['id']) == 1
        assert get_package_like_count(package['id']) == 1

        decrement_resource_like_count('resource_id')
        session.commit()

        assert get_resource_like_count(resource['id']) == 1
        assert get_package_like_count(package['id']) == 1

    def test_increment_decrement_resource_like_count_monthly(self):
        organization = factories.Organization()
        package = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=package['id'])

        today = datetime.now().strftime('%Y-%m-01')

        assert get_resource_like_count_monthly(resource['id'], today) == 0

        increment_resource_like_count_monthly(resource['id'])
        session.commit()

        assert get_resource_like_count_monthly(resource['id'], today) == 1

        increment_resource_like_count_monthly(resource['id'])
        session.commit()

        assert get_resource_like_count_monthly(resource['id'], today) == 2

        decrement_resource_like_count_monthly(resource['id'])
        session.commit()

        assert get_resource_like_count_monthly(resource['id'], today) == 1

        decrement_resource_like_count_monthly('resource_id')
        session.commit()

        assert get_resource_like_count_monthly(resource['id'], today) == 1
