import pytest
from ckan.tests import factories

import ckanext.feedback.services.group.get as get_group_service


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestGetGroupService:
    def test_get_group_names_with_valid_organization(self):
        organization = factories.Organization()

        assert get_group_service.get_group_names() == [organization['name']]
        assert get_group_service.get_group_names(organization['name']) == [
            organization['name']
        ]
        assert get_group_service.get_group_names('test_organization') == []
