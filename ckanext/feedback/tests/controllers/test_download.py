from unittest.mock import patch

import pytest
from ckan import model
from ckan.tests import factories
from flask import Flask

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
    get_engine,
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
        engine = get_engine('db', '5432', 'ckan_test', 'ckan', 'ckan')
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup(self):
        self.resource = factories.Resource()
        self.app = Flask(__name__)

    @patch('ckanext.feedback.controllers.download.download')
    def test_extended_download(self, mocker):
        download = mocker.patch('ckanext.feedback.controllers.download.download')
        with self.app.test_request_context(headers={'Sec-Fetch-Dest': 'document'}):
            DownloadController.extended_download(
                'package_type', self.resource['package_id'], self.resource['id'], None
            )
            assert get_downloads(self.resource['id']) == 1
            assert download

    @patch('ckanext.feedback.controllers.download.download')
    def test_extended_download_with_preview(self, mocker):
        download = mocker.patch('ckanext.feedback.controllers.download.download')

        with self.app.test_request_context(headers={'Sec-Fetch-Dest': 'image'}):
            DownloadController.extended_download(
                'package_type', self.resource['package_id'], self.resource['id'], None
            )
            assert get_downloads(self.resource['id']) is None
            assert download
