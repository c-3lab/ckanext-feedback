import pytest
from ckan import model
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_download_monthly_tables,
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.download import DownloadMonthly
from ckanext.feedback.models.session import session
from ckanext.feedback.services.download.monthly import (
    increment_resource_downloads_monthly,
)


def get_downloads(resource_id):
    count = (
        session.query(DownloadMonthly.download_count)
        .filter(DownloadMonthly.resource_id == resource_id)
        .scalar()
    )
    return count


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestDownloadMonthlyServices:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = model.meta.engine
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)
        create_download_monthly_tables(engine)
        session.commit()

    def test_increment_resource_downloads_monthly(self):
        resource = factories.Resource()
        increment_resource_downloads_monthly(resource['id'])
        assert get_downloads(resource['id']) == 1
        increment_resource_downloads_monthly(resource['id'])
        assert get_downloads(resource['id']) == 2
