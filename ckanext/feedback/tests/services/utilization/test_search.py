import uuid
from datetime import datetime

import ckan.tests.factories as factories
import pytest

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization
from ckanext.feedback.services.utilization.search import (
    get_organization_name_from_pkg,
    get_utilizations,
)


def register_utilization(id, resource_id, title, description, approval, created):
    utilization = Utilization(
        id=id,
        resource_id=resource_id,
        title=title,
        description=description,
        approval=approval,
        created=created,
    )
    session.add(utilization)
    session.commit()


@pytest.mark.db_test
@pytest.mark.usefixtures('with_request_context')
class TestUtilizationDetailsService:

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilizations(self, organization, dataset, resource):
        unapproved_org = factories.Organization(
            is_organization=True,
            name='unapproved_org_name',
            type='organization',
            title='unapproved_org',
        )
        unapproved_dataset = factories.Dataset(owner_org=unapproved_org['id'])
        unapproved_resource = factories.Resource(package_id=unapproved_dataset['id'])
        unapproved_id = str(uuid.uuid4())
        unapproved_title = 'unapproved title'

        approved_org = factories.Organization(
            is_organization=True,
            name='approved_org_name',
            type='organization',
            title='approved_org',
        )
        approved_dataset = factories.Dataset(owner_org=approved_org['id'])
        approved_resource = factories.Resource(package_id=approved_dataset['id'])
        approved_id = str(uuid.uuid4())
        approved_title = 'approved title'

        description = 'test description'

        limit = 20
        offset = 0

        register_utilization(
            unapproved_id,
            unapproved_resource['id'],
            unapproved_title,
            description,
            False,
            datetime(1999, 1, 2, 3, 4),
        )
        register_utilization(
            approved_id,
            approved_resource['id'],
            approved_title,
            description,
            True,
            datetime(2000, 1, 2, 3, 4),
        )

        unapproved_utilization = (
            unapproved_id,
            unapproved_title,
            0,
            datetime(1999, 1, 2, 3, 4),
            False,
            unapproved_resource['name'],
            unapproved_resource['id'],
            unapproved_dataset['title'],
            unapproved_dataset['name'],
            unapproved_org['id'],
            unapproved_org['title'],
            unapproved_org['name'],
            0,
        )

        approved_utilization = (
            approved_id,
            approved_title,
            0,
            datetime(2000, 1, 2, 3, 4),
            True,
            approved_resource['name'],
            approved_resource['id'],
            approved_dataset['title'],
            approved_dataset['name'],
            approved_org['id'],
            approved_org['title'],
            approved_org['name'],
            0,
        )

        # with no argument (sysadmin access - all packages)
        assert get_utilizations(user_orgs='all') == (
            [approved_utilization, unapproved_utilization],
            2,
        )

        # anonymous user - only public packages
        # (both datasets are public by default in factories)
        assert get_utilizations(user_orgs=None) == (
            [approved_utilization, unapproved_utilization],
            2,
        )

        # with package_id (sysadmin access)
        assert get_utilizations(
            package_id=unapproved_dataset['id'], user_orgs='all'
        ) == (
            [unapproved_utilization],
            1,
        )

        # with resource_id (sysadmin access)
        assert get_utilizations(
            resource_id=approved_resource['id'], user_orgs='all'
        ) == (
            [approved_utilization],
            1,
        )

        # with keyword (sysadmin access)
        assert get_utilizations(keyword='unapproved', user_orgs='all') == (
            [unapproved_utilization],
            1,
        )

        # with approval (sysadmin access)
        assert get_utilizations(approval=True, user_orgs='all') == (
            [approved_utilization],
            1,
        )

        # with org_name (sysadmin access)
        assert get_utilizations(org_name=unapproved_org['name'], user_orgs='all') == (
            [unapproved_utilization],
            1,
        )

        # with organization_id (sysadmin access)
        assert get_utilizations(
            admin_owner_orgs=[approved_org['id']], user_orgs='all'
        ) == (
            [approved_utilization],
            1,
        )

        # with organization_id (sysadmin access)
        assert get_utilizations(
            admin_owner_orgs=[unapproved_org['id']], user_orgs='all'
        ) == (
            [
                approved_utilization,
                unapproved_utilization,
            ],
            2,
        )

        # with limit offset (sysadmin access)
        assert get_utilizations(limit=limit, offset=offset, user_orgs='all') == (
            [
                approved_utilization,
                unapproved_utilization,
            ],
            2,
        )

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilizations_with_private_dataset(self):
        org = factories.Organization(
            is_organization=True,
            name='test_org',
            type='organization',
            title='Test Organization',
        )

        # Create a private dataset
        private_dataset = factories.Dataset(
            owner_org=org['id'],
            private=True,
        )
        private_resource = factories.Resource(package_id=private_dataset['id'])
        private_utilization_id = str(uuid.uuid4())

        # Create a public dataset
        public_dataset = factories.Dataset(
            owner_org=org['id'],
            private=False,
        )
        public_resource = factories.Resource(package_id=public_dataset['id'])
        public_utilization_id = str(uuid.uuid4())

        register_utilization(
            private_utilization_id,
            private_resource['id'],
            'private utilization',
            'test description',
            True,
            datetime(2000, 1, 2, 3, 4),
        )
        register_utilization(
            public_utilization_id,
            public_resource['id'],
            'public utilization',
            'test description',
            True,
            datetime(2000, 1, 2, 3, 4),
        )

        # Anonymous user should only see public utilization
        results, count = get_utilizations(user_orgs=None)
        assert count == 1
        assert results[0][0] == public_utilization_id

        # User from different organization should only see public utilization
        other_org = factories.Organization(
            is_organization=True,
            name='other_org',
            type='organization',
        )
        results, count = get_utilizations(user_orgs=[other_org['id']])
        assert count == 1
        assert results[0][0] == public_utilization_id

        # User from same organization should see both
        results, count = get_utilizations(user_orgs=[org['id']])
        assert count == 2

        # Sysadmin should see both
        results, count = get_utilizations(user_orgs='all')
        assert count == 2

    def test_get_organization_name_from_pkg_with_valid_package(
        self, organization, dataset
    ):
        """Test get_organization_name_from_pkg with a valid package ID"""
        # Test with valid package ID using fixtures
        result = get_organization_name_from_pkg(dataset['id'])
        assert result == organization['name']

    def test_get_organization_name_from_pkg_with_invalid_package(self):
        """Test get_organization_name_from_pkg with an invalid package ID"""
        # Test with non-existent package ID
        result = get_organization_name_from_pkg('non_existent_id')
        assert result is None
