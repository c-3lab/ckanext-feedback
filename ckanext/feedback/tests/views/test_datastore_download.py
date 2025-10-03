from unittest.mock import patch

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
    get_datastore_download_blueprint,
    intercept_datastore_download,
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

    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_with_valid_path(
        self, mock_increment_downloads, mock_increment_monthly
    ):
        resource = factories.Resource()

        with self.app.test_request_context(
            f'/datastore/dump/{resource["id"]}', method='GET'
        ):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_called_once_with(resource['id'])
            mock_increment_monthly.assert_called_once_with(resource['id'])
            assert result is None

    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_extracts_resource_id(
        self, mock_increment_downloads, mock_increment_monthly
    ):
        resource_id = 'test-resource-123'

        with self.app.test_request_context(
            f'/datastore/dump/{resource_id}', method='GET'
        ):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_called_once_with(resource_id)
            mock_increment_monthly.assert_called_once_with(resource_id)
            assert result is None

    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_with_query_params(
        self, mock_increment_downloads, mock_increment_monthly
    ):
        resource_id = 'test-resource-456'

        with self.app.test_request_context(
            f'/datastore/dump/{resource_id}?format=csv', method='GET'
        ):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_called_once_with(resource_id)
            mock_increment_monthly.assert_called_once_with(resource_id)
            assert result is None

    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_ignores_non_datastore_request(
        self, mock_increment_downloads, mock_increment_monthly
    ):
        with self.app.test_request_context('/other/path', method='GET'):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_not_called()
            mock_increment_monthly.assert_not_called()
            assert result is None

    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_no_resource_id_match(
        self, mock_increment_downloads, mock_increment_monthly
    ):
        with self.app.test_request_context('/datastore/dump/', method='GET'):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_not_called()
            mock_increment_monthly.assert_not_called()
            assert result is None

    def test_get_datastore_download_blueprint(self):
        blueprint = get_datastore_download_blueprint()

        assert blueprint is not None
        assert blueprint.name == 'feedback_datastore_override'
        assert blueprint.url_prefix == ''

    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_integration(
        self, mock_increment_downloads, mock_increment_monthly
    ):
        resource = factories.Resource()

        initial_count = get_downloads(resource['id'])
        assert initial_count == 0

        with self.app.test_request_context(
            f'/datastore/dump/{resource["id"]}', method='GET'
        ):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_called_once_with(resource['id'])
            mock_increment_monthly.assert_called_once_with(resource['id'])
            assert result is None

    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_handles_post_request(
        self, mock_increment_downloads, mock_increment_monthly
    ):
        resource_id = 'test-resource-789'

        with self.app.test_request_context(
            f'/datastore/dump/{resource_id}', method='POST'
        ):
            result = intercept_datastore_download()

            # POST requests should not increment counters
            mock_increment_downloads.assert_not_called()
            mock_increment_monthly.assert_not_called()
            assert result is None

    @patch('ckanext.feedback.views.datastore_download.log')
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_handles_exception(
        self, mock_increment_downloads, mock_increment_monthly, mock_log
    ):
        resource_id = 'test-resource-error'
        mock_increment_downloads.side_effect = Exception('Test error')

        with self.app.test_request_context(
            f'/datastore/dump/{resource_id}', method='GET'
        ):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_called_once_with(resource_id)
            mock_log.warning.assert_called_once()
            assert result is None
