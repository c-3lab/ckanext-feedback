from unittest.mock import MagicMock, patch

import pytest
from ckan import model
from ckan.tests import factories
from flask import Flask

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.models.session import session
from ckanext.feedback.views.datastore_download import (
    datastore_dump,
    get_datastore_download_blueprint,
)


def get_downloads(resource_id):
    count = (
        session.query(DownloadSummary.download)
        .filter(DownloadSummary.resource_id == resource_id)
        .scalar()
    )
    return count or 0


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestDatastoreDownload:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = model.meta.engine
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)

    @patch('ckanext.feedback.views.datastore_download.original_dump')
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_datastore_dump_with_resource_id(
        self, mock_increment_downloads, mock_increment_monthly, mock_original_dump
    ):
        resource = factories.Resource()
        mock_original_dump.return_value = MagicMock()

        with self.app.test_request_context('/datastore/dump/test-resource-id'):
            datastore_dump(resource['id'])

            mock_increment_downloads.assert_called_once_with(resource['id'])
            mock_increment_monthly.assert_called_once_with(resource['id'])

            mock_original_dump.assert_called_once_with(resource['id'])

    @patch('ckanext.feedback.views.datastore_download.original_dump')
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_datastore_dump_extract_resource_id_from_url(
        self, mock_increment_downloads, mock_increment_monthly, mock_original_dump
    ):
        resource_id = 'test-resource-123'
        mock_original_dump.return_value = MagicMock()

        with self.app.test_request_context(f'/datastore/dump/{resource_id}'):
            datastore_dump()

            mock_increment_downloads.assert_called_once_with(resource_id)
            mock_increment_monthly.assert_called_once_with(resource_id)

            mock_original_dump.assert_called_once_with(resource_id)

    @patch('ckanext.feedback.views.datastore_download.original_dump')
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_datastore_dump_with_query_params(
        self, mock_increment_downloads, mock_increment_monthly, mock_original_dump
    ):
        resource_id = 'test-resource-456'
        mock_original_dump.return_value = MagicMock()

        with self.app.test_request_context(f'/datastore/dump/{resource_id}?format=csv'):
            datastore_dump()

            mock_increment_downloads.assert_called_once_with(resource_id)
            mock_increment_monthly.assert_called_once_with(resource_id)

            mock_original_dump.assert_called_once_with(resource_id)

    @patch('ckanext.feedback.views.datastore_download.original_dump')
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_datastore_dump_non_datastore_request(
        self, mock_increment_downloads, mock_increment_monthly, mock_original_dump
    ):
        with self.app.test_request_context('/other/path'):
            result = datastore_dump()

            mock_increment_downloads.assert_not_called()
            mock_increment_monthly.assert_not_called()

            mock_original_dump.assert_not_called()

            assert result is None

    @patch('ckanext.feedback.views.datastore_download.original_dump')
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_datastore_dump_no_resource_id_match(
        self, mock_increment_downloads, mock_increment_monthly, mock_original_dump
    ):
        mock_original_dump.return_value = MagicMock()

        with self.app.test_request_context('/datastore/dump/'):
            datastore_dump()

            mock_increment_downloads.assert_not_called()
            mock_increment_monthly.assert_not_called()

            mock_original_dump.assert_called_once_with(None)

    def test_get_datastore_download_blueprint(self):
        blueprint = get_datastore_download_blueprint()

        assert blueprint is not None
        assert blueprint.name == 'feedback_datastore_override'
        assert blueprint.url_prefix == ''

    @patch('ckanext.feedback.views.datastore_download.original_dump')
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_datastore_dump_integration_with_database(
        self, mock_increment_downloads, mock_increment_monthly, mock_original_dump
    ):
        resource = factories.Resource()
        mock_original_dump.return_value = MagicMock()

        initial_count = get_downloads(resource['id'])
        assert initial_count == 0

        with self.app.test_request_context(f'/datastore/dump/{resource["id"]}'):
            datastore_dump()

            mock_increment_downloads.assert_called_once_with(resource['id'])
            mock_increment_monthly.assert_called_once_with(resource['id'])
            mock_original_dump.assert_called_once_with(resource['id'])
