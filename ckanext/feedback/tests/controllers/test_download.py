import pytest

from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.controllers.download import DownloadController
from ckanext.feedback.command.feedback import create_utilization_tables, create_resource_tables, create_download_tables, get_engine

from unittest.mock import patch

from flask import Flask
from ckan.tests import factories
from ckan import model

from ckanext.feedback.models.session import session


def get_download_count(resource_id):
    count = (
        session.query(DownloadSummary.download)
        .filter(DownloadSummary.resource_id == resource_id)
        .scalar()
    )
    return count


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestDownloadController():
    model.repo.init_db()
    engine = get_engine('db', '5432', 'ckan_test', 'ckan', 'ckan')
    create_utilization_tables(engine)
    create_resource_tables(engine)
    create_download_tables(engine)

    @pytest.fixture
    def init_table(self):
        resource = factories.Resource()
        yield resource
        session.query(model.resource.Resource).delete()
        session.query(model.package.Package).delete()
        session.commit()

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
