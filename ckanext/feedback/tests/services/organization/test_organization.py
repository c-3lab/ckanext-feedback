import pytest
from ckan import model
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.services.organization import organization

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestOrganization:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_organization(self):
        organization_dict = factories.Organization()
        assert (
            organization.get_organization(organization_dict['id']).id
            == organization_dict['id']
        )

    def test_get_org_list(self):
        organization_dict = factories.Organization()
        id = None

        assert organization.get_org_list(id) == [
            {'name': organization_dict['name'], 'title': organization_dict['title']}
        ]

    def test_get_org_list_by_id(self):
        organization_dict = factories.Organization()
        id = [organization_dict['id']]

        assert organization.get_org_list(id) == [
            {'name': organization_dict['name'], 'title': organization_dict['title']}
        ]
