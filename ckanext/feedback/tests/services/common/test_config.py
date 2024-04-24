import pytest
from ckan import model
import ckan.tests.factories as factories

from ckanext.feedback.services.common.config import get_organization

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestCheck:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()

    def test_check_administrator(self):
        example_organization = factories.Organization(
            is_organization=True,
            name='org_name',
            type='organization',
            title='org_title',
        )

        result = get_organization(example_organization['id'])
        assert result.name == example_organization['name']
