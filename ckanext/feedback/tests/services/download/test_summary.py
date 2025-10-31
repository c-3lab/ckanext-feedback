from datetime import datetime

import pytest

from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.models.session import session
from ckanext.feedback.services.download.summary import (
    get_package_downloads,
    get_resource_downloads,
    increment_resource_downloads,
)


def get_downloads(resource_id):
    return (
        session.query(DownloadSummary)
        .filter(DownloadSummary.resource_id == resource_id)
        .first()
    )


@pytest.mark.db_test
class TestDownloadServices:
    def test_get_package_download(self, resource, download_summary):
        assert (
            get_package_downloads(resource['package_id']) == download_summary.download
        )

    def test_get_resource_download(self, resource, download_summary):
        assert get_resource_downloads(resource['id']) == download_summary.download

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_increment_resource_downloads(self, resource):
        increment_resource_downloads(resource['id'])
        session.commit()
        session.expire_all()
        download_summary = get_downloads(resource['id'])

        assert download_summary.download == 1
        assert download_summary.updated is None

        increment_resource_downloads(resource['id'])
        session.commit()
        session.expire_all()
        download_summary = get_downloads(resource['id'])

        assert download_summary.download == 2
        assert download_summary.updated == datetime(2024, 1, 1, 15, 0, 0)
