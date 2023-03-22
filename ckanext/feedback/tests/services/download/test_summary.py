import pytest

from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.services.download.summary import (
    get_package_downloads,
    get_resource_downloads,
    increment_resource_downloads
)

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


class TestDownloadView:
    @pytest.fixture
    def init_table(self):
        resource = factories.Resource()
        yield resource
        session.query(model.resource.Resource).delete()
        session.query(model.package.Package).delete()
        session.query(DownloadSummary).delete()
        session.commit()

    def test_increment_resource_downloads(self, init_table):
        increment_resource_downloads(init_table['id'])
        assert get_download_count(init_table['id']) == 1
        increment_resource_downloads(init_table['id'])
        assert get_download_count(init_table['id']) == 2

    def test_get_package_download(self, init_table):
        assert get_package_downloads(init_table['package_id']) == 0
        download_summary = DownloadSummary(
            id=str('test_id'),
            resource_id=init_table['id'],
            download=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(download_summary)
        assert get_package_downloads(init_table['package_id']) == 1

    def test_get_resource_download(self, init_table):
        assert get_resource_downloads(init_table['id']) == 0
        download_summary = DownloadSummary(
            id=str('test_id'),
            resource_id=init_table['id'],
            download=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(download_summary)
        assert get_resource_downloads(init_table['id']) == 1
