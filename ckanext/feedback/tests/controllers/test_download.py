import pytest

from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.controllers.download import DownloadController
from flask import session

from ckanext.feedback.services.download.summary import increment_resource_downloads
from unittest.mock import Mock, MagicMock, patch
from ckanext.feedback.command.feedback import get_engine, engine
from ckanext.feedback.models.session import Base

from ckan.tests import factories
from ckan import model

from ckanext.feedback.models.session import session
from flask import Flask, request


def get_download_count(resource_id):
    count = (
        session.query(DownloadSummary.download)
        .filter(DownloadSummary.resource_id == resource_id)
        .scalar()
    )
    return count


# engine = get_engine('db', 5432, 'ckan', 'ckan', 'ckan')


class TestDownloadController:
    @pytest.fixture(autouse=True)
    def init_table(self):
        DownloadSummary.__table__.create(engine)
        resource = factories.Resource()
        yield resource
        DownloadSummary.__table__.drop(engine, checkfirst=True)

    def test_increment_resource_download(self, init_table):
        DownloadController.increment_resource_downloads(init_table['id'])
        assert get_download_count(init_table['id']) == 1

    @patch('ckanext.feedback.controllers.download.download')
    def test_extended_download(self, mocker, init_table):
        self.app = Flask(__name__)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.ctx.pop()
        download = mocker.patch('ckanext.feedback.controllers.download.download')

        with self.app.test_request_context(headers={'Sec-Fetch-Dest': 'image'}):
            DownloadController.extended_download('package_type', init_table['package_id'], init_table['id'], None)
            assert get_download_count(init_table['id']) is None
            assert download

        with self.app.test_request_context(headers={'Sec-Fetch-Dest': 'document'}):
            DownloadController.extended_download('package_type', init_table['package_id'], init_table['id'], None)
            assert get_download_count(init_table['id']) == 1
            assert download
            