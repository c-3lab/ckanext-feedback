from unittest.mock import patch

import ckan.tests.factories as factories
import pytest
from ckan import model
from ckan.plugins import toolkit

from ckanext.feedback.services.common.config import (
    CONFIG_HANDLER_PATH,
    download_handler,
    get_organization,
)

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

    @patch('ckanext.feedback.services.common.config.import_string')
    def test_seted_download_handler(self, mock_import_string):
        toolkit.config['ckan.feedback.download_handler'] = CONFIG_HANDLER_PATH
        download_handler()
        mock_import_string.assert_called_once_with(CONFIG_HANDLER_PATH, silent=True)
