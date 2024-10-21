from unittest.mock import patch

import pytest
from ckan import model
from ckan.common import config
from ckan.tests import factories
from flask import Flask

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.models.session import session
from ckanext.feedback.views.download import download


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
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)

    @patch('ckanext.feedback.views.download.DownloadController.extended_download')
    def test_download_true(self, mock_extended_download):
        resource = factories.Resource()
        mock_extended_download.return_value = mock_extended_download

        # with self.app.test_request_context(headers={'Sec-Fetch-Dest': 'document'}):
        download(
            'package_type', resource['package_id'], resource['id'], resource['url']
        )
        mock_extended_download.assert_called_once_with(
            package_type='package_type',
            id=resource['package_id'],
            resource_id=resource['id'],
            filename=resource['url'],
        )

    @patch('ckanext.feedback.views.download.download_handler')
    @patch('ckanext.feedback.views.download.resource.download')
    def test_download_false_with_not_set_download_handler(
        self, mock_download, mock_download_handler
    ):
        resource = factories.Resource()
        mock_download_handler.return_value = None
        config['ckan.feedback.downloads.enable'] = False

        download(
            'package_type', resource['package_id'], resource['id'], resource['url']
        )
        mock_download.assert_called_once_with(
            package_type='package_type',
            id=resource['package_id'],
            resource_id=resource['id'],
            filename=resource['url'],
        )

    @patch('ckanext.feedback.views.download.download_handler')
    @patch('ckanext.feedback.views.download.DownloadController.extended_download')
    def test_download_false_with_set_download_handler(
        self, mock_extended_download, mock_download_handler
    ):
        owner_org = factories.Organization()
        dataset = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(package_id=dataset['id'])
        mock_download_handler.return_value = mock_extended_download
        config['ckan.feedback.downloads.enable'] = False

        download('package_type', resource['package_id'], resource['id'], None)
        mock_download_handler.assert_called_once_with()
