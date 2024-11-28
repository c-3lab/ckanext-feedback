import logging

import pytest
from ckan import model
from ckan.tests import factories

import ckanext.feedback.services.ranking.dataset as dataset_ranking_service
from ckanext.feedback.command.feedback import (
    create_download_monthly_tables,
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.download import DownloadMonthly, DownloadSummary
from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestRankingDataset:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = model.meta.engine
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)
        create_download_monthly_tables(engine)

    def test_get_download_ranking(self):
        organization = factories.Organization()
        package = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=package['id'])

        top_ranked_limit = '1'
        start_year_month = '2023-01'
        end_year_month = '2023-12'
        enable_org = [organization['name']]

        assert (
            dataset_ranking_service.get_download_ranking(
                top_ranked_limit, start_year_month, end_year_month, enable_org
            )
            == []
        )

        download_summary = DownloadSummary(
            id=str('test_id'),
            resource_id=resource['id'],
            download=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(download_summary)

        download_monthly = DownloadMonthly(
            id=str('test_id'),
            resource_id=resource['id'],
            download_count=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(download_monthly)
        session.commit()

        assert dataset_ranking_service.get_download_ranking(
            top_ranked_limit, start_year_month, end_year_month, enable_org
        ) == [
            (
                organization['name'],
                organization['title'],
                package['name'],
                package['title'],
                package['notes'],
                1,
                1,
            )
        ]

    def test_get_download_ranking_enable_org_none(self):
        organization = factories.Organization()
        package = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=package['id'])

        top_ranked_limit = '1'
        start_year_month = '2023-01'
        end_year_month = '2023-12'
        enable_org = []

        assert (
            dataset_ranking_service.get_download_ranking(
                top_ranked_limit, start_year_month, end_year_month, enable_org
            )
            == []
        )

        download_summary = DownloadSummary(
            id=str('test_id'),
            resource_id=resource['id'],
            download=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(download_summary)

        download_monthly = DownloadMonthly(
            id=str('test_id'),
            resource_id=resource['id'],
            download_count=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(download_monthly)
        session.commit()

        assert dataset_ranking_service.get_download_ranking(
            top_ranked_limit, start_year_month, end_year_month, enable_org
        ) == [
            (
                organization['name'],
                organization['title'],
                package['name'],
                package['title'],
                package['notes'],
                1,
                1,
            )
        ]
