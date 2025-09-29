import logging

import pytest

import ckanext.feedback.services.ranking.dataset as dataset_ranking_service
from ckanext.feedback.models.download import DownloadMonthly, DownloadSummary
from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


@pytest.mark.db_test
@pytest.mark.usefixtures('with_plugins', 'with_request_context')
class TestRankingDataset:

    def test_get_download_ranking(self, organization, dataset, resource):
        assert (
            dataset_ranking_service.get_generic_ranking(
                1,
                '2023-01',
                '2023-12',
                DownloadMonthly,
                'download_count',
                DownloadSummary,
                'download',
                [organization['name']],
            )
            == []
        )

        session.add(
            DownloadSummary(
                id='sum1',
                resource_id=resource['id'],
                download=1,
                created='2023-03-31 01:23:45',
                updated='2023-03-31 01:23:45',
            )
        )
        session.add(
            DownloadMonthly(
                id='mon1',
                resource_id=resource['id'],
                download_count=1,
                created='2023-03-31 01:23:45',
                updated='2023-03-31 01:23:45',
            )
        )
        session.commit()

        result = dataset_ranking_service.get_generic_ranking(
            1,
            '2023-01',
            '2023-12',
            DownloadMonthly,
            'download_count',
            DownloadSummary,
            'download',
            [organization['name']],
        )
        assert len(result) == 1

    def test_get_download_ranking_enable_org_none(
        self, organization, dataset, resource
    ):
        assert (
            dataset_ranking_service.get_generic_ranking(
                1,
                '2023-01',
                '2023-12',
                DownloadMonthly,
                'download_count',
                DownloadSummary,
                'download',
                [],
            )
            == []
        )

        session.add(
            DownloadSummary(
                id='sum1',
                resource_id=resource['id'],
                download=1,
                created='2023-03-31 01:23:45',
                updated='2023-03-31 01:23:45',
            )
        )
        session.add(
            DownloadMonthly(
                id='mon1',
                resource_id=resource['id'],
                download_count=1,
                created='2023-03-31 01:23:45',
                updated='2023-03-31 01:23:45',
            )
        )
        session.commit()

        result = dataset_ranking_service.get_generic_ranking(
            1,
            '2023-01',
            '2023-12',
            DownloadMonthly,
            'download_count',
            DownloadSummary,
            'download',
            [],
        )
        assert len(result) == 1

    def test_get_download_ranking_sorted_and_limited(
        self, organization_factory, package_factory, resource_factory
    ):
        org_a = organization_factory()
        org_b = organization_factory()
        pkg_a = package_factory(owner_org=org_a['id'])
        pkg_b = package_factory(owner_org=org_b['id'])
        res_a = resource_factory(package_id=pkg_a['id'])
        res_b = resource_factory(package_id=pkg_b['id'])

        session.add(
            DownloadSummary(
                id='sum_a',
                resource_id=res_a['id'],
                download=5,
                created='2023-03-31 01:23:45',
                updated='2023-03-31 01:23:45',
            )
        )
        session.add(
            DownloadMonthly(
                id='mon_a',
                resource_id=res_a['id'],
                download_count=5,
                created='2023-03-31 01:23:45',
                updated='2023-03-31 01:23:45',
            )
        )
        session.add(
            DownloadSummary(
                id='sum_b',
                resource_id=res_b['id'],
                download=2,
                created='2023-03-31 01:23:45',
                updated='2023-03-31 01:23:45',
            )
        )
        session.add(
            DownloadMonthly(
                id='mon_b',
                resource_id=res_b['id'],
                download_count=2,
                created='2023-03-31 01:23:45',
                updated='2023-03-31 01:23:45',
            )
        )
        session.commit()

        result = dataset_ranking_service.get_generic_ranking(
            1,
            '2023-01',
            '2023-12',
            DownloadMonthly,
            'download_count',
            DownloadSummary,
            'download',
            [org_a['name'], org_b['name']],
        )
        assert len(result) == 1
        assert result[0][0] == org_a['name']

    def test_get_download_ranking_filter_by_organization_name(
        self, organization_factory, package_factory, resource_factory
    ):
        org_a = organization_factory()
        org_b = organization_factory()
        pkg_a = package_factory(owner_org=org_a['id'])
        pkg_b = package_factory(owner_org=org_b['id'])
        res_a = resource_factory(package_id=pkg_a['id'])
        res_b = resource_factory(package_id=pkg_b['id'])

        session.add(
            DownloadSummary(
                id='sum_a2',
                resource_id=res_a['id'],
                download=1,
                created='2023-03-31 00:00:00',
                updated='2023-03-31 00:00:00',
            )
        )
        session.add(
            DownloadMonthly(
                id='mon_a2',
                resource_id=res_a['id'],
                download_count=1,
                created='2023-03-01 00:00:00',
                updated='2023-03-01 00:00:00',
            )
        )
        session.add(
            DownloadSummary(
                id='sum_b2',
                resource_id=res_b['id'],
                download=1,
                created='2023-03-31 00:00:00',
                updated='2023-03-31 00:00:00',
            )
        )
        session.add(
            DownloadMonthly(
                id='mon_b2',
                resource_id=res_b['id'],
                download_count=1,
                created='2023-03-01 00:00:00',
                updated='2023-03-01 00:00:00',
            )
        )
        session.commit()

        result = dataset_ranking_service.get_generic_ranking(
            10,
            '2023-01',
            '2023-12',
            DownloadMonthly,
            'download_count',
            DownloadSummary,
            'download',
            [org_a['name'], org_b['name']],
            organization_name=org_a['name'],
        )
        assert len(result) == 1
        assert result[0][0] == org_a['name']

    def test_get_download_ranking_enable_org_none_list(
        self, organization, package, resource
    ):
        session.add(
            DownloadSummary(
                id=str('sum_none'),
                resource_id=resource['id'],
                download=1,
                created='2023-03-31 01:23:45.123456',
                updated='2023-03-31 01:23:45.123456',
            )
        )
        session.add(
            DownloadMonthly(
                id=str('mon_none'),
                resource_id=resource['id'],
                download_count=1,
                created='2023-03-31 01:23:45.123456',
                updated='2023-03-31 01:23:45.123456',
            )
        )
        session.commit()

        result = dataset_ranking_service.get_generic_ranking(
            10,
            '2023-01',
            '2023-12',
            DownloadMonthly,
            'download_count',
            DownloadSummary,
            'download',
            [None],
        )
        assert len(result) == 1
        assert result[0][0] == organization['name']

    def test_get_download_ranking_date_range_inclusive(
        self, organization, package, resource
    ):
        session.add(
            DownloadSummary(
                id=str('sum_edge1'),
                resource_id=resource['id'],
                download=100,
                created='2023-03-31 23:59:59',
                updated='2023-03-31 23:59:59',
            )
        )
        session.add(
            DownloadMonthly(
                id=str('mon_edge1'),
                resource_id=resource['id'],
                download_count=1,
                created='2023-03-01 00:00:00',
                updated='2023-03-01 00:00:00',
            )
        )
        session.add(
            DownloadMonthly(
                id=str('mon_out1'),
                resource_id=resource['id'],
                download_count=99,
                created='2023-02-28 23:59:59',
                updated='2023-02-28 23:59:59',
            )
        )
        session.commit()

        result = dataset_ranking_service.get_generic_ranking(
            10,
            '2023-03',
            '2023-03',
            DownloadMonthly,
            'download_count',
            DownloadSummary,
            'download',
            [organization['name']],
        )

        assert len(result) == 1
        assert result[0][5] == 1
        assert result[0][6] == 100

    def test_get_download_ranking_excludes_inactive_package_or_group(
        self, organization, package_factory, resource_factory
    ):
        pkg = package_factory(owner_org=organization['id'], state='deleted')
        res = resource_factory(package_id=pkg['id'])

        session.add(
            DownloadSummary(
                id='sum_inactive_pkg',
                resource_id=res['id'],
                download=1,
                created='2023-03-31 00:00:00',
                updated='2023-03-31 00:00:00',
            )
        )
        session.add(
            DownloadMonthly(
                id='mon_inactive_pkg',
                resource_id=res['id'],
                download_count=1,
                created='2023-03-01 00:00:00',
                updated='2023-03-01 00:00:00',
            )
        )
        session.commit()

        result = dataset_ranking_service.get_generic_ranking(
            10,
            '2023-01',
            '2023-12',
            DownloadMonthly,
            'download_count',
            DownloadSummary,
            'download',
            [organization['name']],
        )
        assert result == []

    def test_get_last_day_of_month(self):
        assert dataset_ranking_service.get_last_day_of_month(2023, 1) == 31
        assert dataset_ranking_service.get_last_day_of_month(2023, 2) == 28
        assert dataset_ranking_service.get_last_day_of_month(2024, 2) == 29

    def test_no_result_if_only_period_or_only_total_exists(
        self, organization, package, resource
    ):
        session.add(
            DownloadMonthly(
                id=str('mon_only'),
                resource_id=resource['id'],
                download_count=1,
                created='2023-03-31 00:00:00',
                updated='2023-03-31 00:00:00',
            )
        )
        session.commit()

        result1 = dataset_ranking_service.get_generic_ranking(
            10,
            '2023-01',
            '2023-12',
            DownloadMonthly,
            'download_count',
            DownloadSummary,
            'download',
            [organization['name']],
        )
        assert result1 == []

        session.query(DownloadMonthly).delete()
        session.add(
            DownloadSummary(
                id=str('sum_only'),
                resource_id=resource['id'],
                download=1,
                created='2023-03-31 00:00:00',
                updated='2023-03-31 00:00:00',
            )
        )
        session.commit()

        result2 = dataset_ranking_service.get_generic_ranking(
            10,
            '2023-01',
            '2023-12',
            DownloadMonthly,
            'download_count',
            DownloadSummary,
            'download',
            [organization['name']],
        )
        assert result2 == []
