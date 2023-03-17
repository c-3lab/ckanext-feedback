import pytest

from ckanext.feedback.models.download import DownloadSummary

from ckan.tests import factories
from ckan import model

from ckanext.feedback.models.session import session


class TestDownloadModel:

    @pytest.fixture
    def init_table(requests):
        resource = factories.Resource()
        yield resource
        session.query(model.resource.Resource).delete()
        session.query(model.package.Package).delete()
        session.commit()

    def test_model(self, init_table):
        download_summary = DownloadSummary(
            id=str('test_id'),
            resource_id=init_table['id'],
            download=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(download_summary)

        assert isinstance(download_summary, DownloadSummary)
        assert download_summary.id == 'test_id'
        assert download_summary.resource_id == init_table['id']
        assert download_summary.download == 1
        assert download_summary.created == '2023-03-31 01:23:45.123456'
        assert download_summary.updated == '2023-03-31 01:23:45.123456'
