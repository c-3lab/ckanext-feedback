import pytest

from ckanext.feedback.services.organization import organization as organization_service


@pytest.mark.db_test
class TestOrganization:
    def test_get_organization(self, organization):
        result = organization_service.get_organization(organization['id'])
        assert result.id == organization['id']

    def test_get_org_list_without_id(self, organization):
        result = organization_service.get_org_list()
        assert result == [
            {'name': organization['name'], 'title': organization['title']}
        ]

    def test_get_org_list_with_id(self, organization):
        result = organization_service.get_org_list([organization['id']])

        assert result == [
            {'name': organization['name'], 'title': organization['title']}
        ]

    def test_get_organization_name_list(self, organization):
        result = organization_service.get_organization_name_list()
        assert result == [organization['name']]

    def test_get_organization_name_by_name(self, organization):
        result = organization_service.get_organization_name_by_name(
            organization['name']
        )
        assert result == (organization['name'],)

    def test_get_organization_name_by_id(self, organization):
        result = organization_service.get_organization_name_by_id(organization['id'])
        assert result == (organization['name'],)
