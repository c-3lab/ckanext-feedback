import pytest

from ckanext.feedback.models.download import DownloadSummary

from ckan.tests import factories

from ckanext.feedback.models.session import Base, session


class Test:
    @pytest.fixture(autouse=True)
    def init_table(self):
        Base.metadata.create_all(Base.metadata.engine)

    @pytest.mark.usefixtures("init_table")
    def create_table(self):
        resource = factories.Resource()
        download_summary = DownloadSummary(
            id=str('test_id'),
            resource_id=resource['id'],
            download=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(download_summary)

        assert isinstance(download_summary, DownloadSummary)
        assert download_summary.id == 'test_id'
        assert download_summary.resource_id == resource['id']
        assert download_summary.download == 1
        assert download_summary.created == '2023-03-31 01:23:45.123456'
        assert download_summary.updated == '2023-03-31 01:23:45.123456'
