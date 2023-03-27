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
    model.repo.init_db()
    engine = get_engine('db', '5432', 'ckan_test', 'ckan', 'ckan')
    create_utilization_tables(engine)
    create_resource_tables(engine)
    create_download_tables(engine)

    def test_increment_resource_download(self):
        resource = factories.Resource()
        DownloadController.increment_resource_downloads(resource['id'])
        assert get_downloads(resource['id']) == 1

    @patch('ckanext.feedback.controllers.download.download')
    def test_extended_download(self, mocker):
        resource = factories.Resource()
        self.app = Flask(__name__)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.ctx.pop()
        download = mocker.patch('ckanext.feedback.controllers.download.download')

        with self.app.test_request_context(headers={'Sec-Fetch-Dest': 'image'}):
            DownloadController.extended_download(
                'package_type', resource['package_id'], resource['id'], None
            )
            assert get_downloads(resource['id']) is None
            assert download

        with self.app.test_request_context(headers={'Sec-Fetch-Dest': 'document'}):
            DownloadController.extended_download(
                'package_type', resource['package_id'], resource['id'], None
            )
            assert get_downloads(resource['id']) == 1
            assert download
