from unittest.mock import MagicMock, patch

import pytest
import requests
from ckan import model
from ckan.tests import factories
from flask import Flask

from ckanext.feedback.command.feedback import (
    create_download_monthly_tables,
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.download import DownloadController
from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.models.session import session


def get_downloads(resource_id):
    count = (
        session.query(DownloadSummary.download)
        .filter(DownloadSummary.resource_id == resource_id)
        .scalar()
    )
    return count


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestDownloadController:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = model.meta.engine
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)
        create_download_monthly_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)

    @patch('ckanext.feedback.controllers.download.feedback_config.download_handler')
    @patch('ckanext.feedback.controllers.download.resource.download')
    def test_extended_download(self, mock_download, mock_download_handler):
        owner_org = factories.Organization()
        dataset = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(package_id=dataset['id'])
        mock_download_handler.return_value = None

        with self.app.test_request_context(
            '/?user-download=true', headers={'Sec-Fetch-Dest': 'document'}
        ):
            DownloadController.extended_download(
                'package_type', resource['package_id'], resource['id'], None
            )
            assert get_downloads(resource['id']) == 1
            mock_download.assert_called_once_with(
                package_type='package_type',
                id=resource['package_id'],
                resource_id=resource['id'],
                filename=resource['url'],
            )

    @patch('ckanext.feedback.controllers.download.resource.download')
    def test_extended_download_with_preview(self, mock_download):
        resource = factories.Resource()
        with self.app.test_request_context(headers={'Sec-Fetch-Dest': 'image'}):
            DownloadController.extended_download(
                'package_type', resource['package_id'], resource['id'], resource['url']
            )
            assert get_downloads(resource['id']) is None
            assert mock_download

    @patch('ckanext.feedback.controllers.download.feedback_config.download_handler')
    @patch('ckanext.feedback.controllers.download.resource.download')
    def test_extended_download_with_set_download_handler(
        self, handler, mock_download_handler
    ):
        resource = factories.Resource()
        mock_download_handler.return_value = handler
        with self.app.test_request_context(
            '/?user-download=true', headers={'Sec-Fetch-Dest': 'image'}
        ):
            DownloadController.extended_download(
                'package_type', resource['package_id'], resource['id'], resource['url']
            )
            handler.assert_called_once_with(
                package_type='package_type',
                id=resource['package_id'],
                resource_id=resource['id'],
                filename=resource['url'],
            )

    @patch('ckanext.feedback.controllers.download.feedback_config.download_handler')
    @patch('ckanext.feedback.controllers.download.resource.download')
    @patch('ckanext.feedback.controllers.download.requests.get')
    @patch('ckanext.feedback.controllers.download.Response')
    def test_extended_download_get_redirect_resource(
        self, mock_Response, mock_requests_get, mock_download, mock_download_handler
    ):
        owner_org = factories.Organization()
        dataset = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(package_id=dataset['id'])
        mock_download_handler.return_value = None

        mock_responce = MagicMock()
        mock_responce.status_code = 302
        mock_responce.headers.get.return_value = 'http://mock_url.com/mock.txt'
        mock_download.return_value = mock_responce

        mock_requests_get.return_value = MagicMock()

        mock_external_response = MagicMock()
        mock_external_response.status_code = 200
        mock_external_response.headers.get.return_value = 'filename="mock.txt"'
        mock_Response.return_value = mock_external_response

        with self.app.test_request_context(
            '/?user-download=true', headers={'Sec-Fetch-Dest': 'document'}
        ):
            DownloadController.extended_download(
                'package_type', resource['package_id'], resource['id'], None
            )
            assert get_downloads(resource['id']) == 1
            mock_download.assert_called_once_with(
                package_type='package_type',
                id=resource['package_id'],
                resource_id=resource['id'],
                filename=resource['url'],
            )

    @patch('ckanext.feedback.controllers.download.feedback_config.download_handler')
    @patch('ckanext.feedback.controllers.download.resource.download')
    @patch('ckanext.feedback.controllers.download.requests.get')
    @patch('ckanext.feedback.controllers.download.Response')
    def test_extended_download_get_redirect_resource_non_filename(
        self, mock_Response, mock_requests_get, mock_download, mock_download_handler
    ):
        owner_org = factories.Organization()
        dataset = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(package_id=dataset['id'])
        mock_download_handler.return_value = None

        mock_responce = MagicMock()
        mock_responce.status_code = 302
        mock_responce.headers.get.return_value = 'http://mock_url.com/mock.txt'
        mock_download.return_value = mock_responce

        mock_requests_get.return_value = MagicMock()

        mock_external_response = MagicMock()
        mock_external_response.status_code = 200
        mock_external_response.headers.get.return_value = ''
        mock_Response.return_value = mock_external_response

        with self.app.test_request_context(
            '/?user-download=true', headers={'Sec-Fetch-Dest': 'document'}
        ):
            DownloadController.extended_download(
                'package_type', resource['package_id'], resource['id'], None
            )
            assert get_downloads(resource['id']) == 1
            mock_download.assert_called_once_with(
                package_type='package_type',
                id=resource['package_id'],
                resource_id=resource['id'],
                filename=resource['url'],
            )

    @patch('ckanext.feedback.controllers.download.feedback_config.download_handler')
    @patch('ckanext.feedback.controllers.download.resource.download')
    @patch('ckanext.feedback.controllers.download.requests.get')
    @patch('ckanext.feedback.controllers.download.Response')
    def test_extended_download_redirect_resource_ConnectionError(
        self, mock_Response, mock_requests_get, mock_download, mock_download_handler
    ):
        owner_org = factories.Organization()
        dataset = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(package_id=dataset['id'])
        mock_download_handler.return_value = None

        mock_responce = MagicMock()
        mock_responce.status_code = 302
        mock_responce.headers.get.return_value = 'http://mock_url.com/mock.txt'
        mock_download.return_value = mock_responce

        mock_requests_get.side_effect = requests.exceptions.ConnectionError()

        mock_external_response = MagicMock()
        mock_external_response.status_code = 200
        mock_external_response.headers.get.return_value = ''
        mock_Response.return_value = mock_external_response

        with self.app.test_request_context(
            '/?user-download=true', headers={'Sec-Fetch-Dest': 'document'}
        ):
            DownloadController.extended_download(
                'package_type', resource['package_id'], resource['id'], None
            )
            assert get_downloads(resource['id']) == 1
            mock_download.assert_called_once_with(
                package_type='package_type',
                id=resource['package_id'],
                resource_id=resource['id'],
                filename=resource['url'],
            )

    @patch('ckanext.feedback.controllers.download.feedback_config.download_handler')
    @patch('ckanext.feedback.controllers.download.resource.download')
    @patch('ckanext.feedback.controllers.download.requests.get')
    @patch('ckanext.feedback.controllers.download.Response')
    def test_extended_download_without_redirect_resource(
        self, mock_Response, mock_requests_get, mock_download, mock_download_handler
    ):
        owner_org = factories.Organization()
        dataset = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(package_id=dataset['id'])
        mock_download_handler.return_value = None

        mock_responce = MagicMock()
        mock_responce.status_code = 302
        mock_responce.headers.get.return_value = 'http://mock_url.com/mock.txt'
        mock_download.return_value = mock_responce

        mock_requests_get.return_value = MagicMock()

        mock_external_response = MagicMock()
        mock_external_response.status_code = 500
        mock_external_response.headers.get.return_value = ''
        mock_Response.return_value = mock_external_response

        with self.app.test_request_context(
            '/?user-download=true', headers={'Sec-Fetch-Dest': 'document'}
        ):
            DownloadController.extended_download(
                'package_type', resource['package_id'], resource['id'], None
            )
            assert get_downloads(resource['id']) == 1
            mock_download.assert_called_once_with(
                package_type='package_type',
                id=resource['package_id'],
                resource_id=resource['id'],
                filename=resource['url'],
            )
