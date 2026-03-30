from unittest.mock import MagicMock, patch

from ckanext.feedback.services.package.summary import (
    get_package_feedback_stats_bulk,
    get_package_id_from_packages,
)


class TestSummary:
    def test_get_package_id_from_packages_with_none(self):
        assert get_package_id_from_packages(None) is None

    def test_get_package_id_from_packages_with_empty_dict(self):
        assert get_package_id_from_packages({}) is None

    def test_get_package_id_from_packages_with_dict_having_id(self):
        assert get_package_id_from_packages({'id': 'abc-123'}) == 'abc-123'

    def test_get_package_id_from_packages_with_dict_without_id(self):
        assert get_package_id_from_packages({'name': 'test-dataset'}) is None

    def test_get_package_id_from_packages_with_object_having_id(self):
        obj = MagicMock()
        obj.id = 'abc-123'
        assert get_package_id_from_packages(obj) == 'abc-123'

    def test_get_package_id_from_packages_with_object_without_id(self):
        obj = MagicMock(spec=[])
        assert get_package_id_from_packages(obj) is None

    def test_get_package_id_from_packages_with_id_as_whitespace(self):
        assert get_package_id_from_packages({'id': '   '}) is None

    def test_get_package_id_from_packages_with_id_as_string_none(self):
        assert get_package_id_from_packages({'id': 'None'}) is None

    def test_get_package_id_from_packages_with_id_none_value(self):
        assert get_package_id_from_packages({'id': None}) is None

    def test_get_package_feedback_stats_bulk_with_empty_list(self):
        assert get_package_feedback_stats_bulk([]) == {}

    @patch('ckanext.feedback.services.package.summary.resource_likes_service')
    @patch('ckanext.feedback.services.package.summary.download_summary_service')
    @patch('ckanext.feedback.services.package.summary.utilization_summary_service')
    @patch('ckanext.feedback.services.package.summary.resource_summary_service')
    def test_get_package_feedback_stats_bulk_with_all_invalid_packages(
        self,
        mock_resource_summary_service,
        mock_utilization_summary_service,
        mock_download_summary_service,
        mock_resource_likes_service,
    ):
        result = get_package_feedback_stats_bulk([None, {}])
        assert result == {}
        mock_resource_likes_service.get_package_like_count_bulk.assert_not_called()

        result = get_package_feedback_stats_bulk([{'name': 'test-dataset'}])
        assert result == {}
        mock_resource_likes_service.get_package_like_count_bulk.assert_not_called()

    @patch('ckanext.feedback.services.package.summary.resource_likes_service')
    @patch('ckanext.feedback.services.package.summary.download_summary_service')
    @patch('ckanext.feedback.services.package.summary.utilization_summary_service')
    @patch('ckanext.feedback.services.package.summary.resource_summary_service')
    def test_get_package_feedback_stats_bulk_with_rating_zero(
        self,
        mock_resource_summary_service,
        mock_utilization_summary_service,
        mock_download_summary_service,
        mock_resource_likes_service,
    ):
        pid = 'abc-123'
        mock_resource_likes_service.get_package_like_count_bulk.return_value = {pid: 5}
        mock_download_summary_service.get_package_downloads_bulk.return_value = {
            pid: 10
        }
        mock_utilization_summary_service.get_package_utilizations_bulk.return_value = {
            pid: 3
        }
        issue_resolutions_bulk = (
            mock_utilization_summary_service.get_package_issue_resolutions_bulk
        )
        issue_resolutions_bulk.return_value = {pid: 1}
        mock_resource_summary_service.get_package_comments_bulk.return_value = {pid: 7}
        mock_resource_summary_service.get_package_rating_bulk.return_value = {pid: 0}

        result = get_package_feedback_stats_bulk([{'id': pid}])
        assert result == {
            pid: {
                'like_count': 5,
                'downloads': 10,
                'utilizations': 3,
                'comments': 7,
                'rating': 0,
                'issue_resolutions': 1,
            }
        }

    @patch('ckanext.feedback.services.package.summary.resource_likes_service')
    @patch('ckanext.feedback.services.package.summary.download_summary_service')
    @patch('ckanext.feedback.services.package.summary.utilization_summary_service')
    @patch('ckanext.feedback.services.package.summary.resource_summary_service')
    def test_get_package_feedback_stats_bulk_with_rating_nonzero(
        self,
        mock_resource_summary_service,
        mock_utilization_summary_service,
        mock_download_summary_service,
        mock_resource_likes_service,
    ):
        pid = 'abc-123'
        mock_resource_likes_service.get_package_like_count_bulk.return_value = {pid: 2}
        mock_download_summary_service.get_package_downloads_bulk.return_value = {pid: 4}
        mock_utilization_summary_service.get_package_utilizations_bulk.return_value = {
            pid: 1
        }
        issue_resolutions_bulk = (
            mock_utilization_summary_service.get_package_issue_resolutions_bulk
        )
        issue_resolutions_bulk.return_value = {pid: 0}
        mock_resource_summary_service.get_package_comments_bulk.return_value = {pid: 6}
        mock_resource_summary_service.get_package_rating_bulk.return_value = {
            pid: 4.666
        }

        result = get_package_feedback_stats_bulk([{'id': pid}])
        assert result == {
            pid: {
                'like_count': 2,
                'downloads': 4,
                'utilizations': 1,
                'comments': 6,
                'rating': 4.7,
                'issue_resolutions': 0,
            }
        }

    @patch('ckanext.feedback.services.package.summary.resource_likes_service')
    @patch('ckanext.feedback.services.package.summary.download_summary_service')
    @patch('ckanext.feedback.services.package.summary.utilization_summary_service')
    @patch('ckanext.feedback.services.package.summary.resource_summary_service')
    def test_get_package_feedback_stats_bulk_with_mixed_packages(
        self,
        mock_resource_summary_service,
        mock_utilization_summary_service,
        mock_download_summary_service,
        mock_resource_likes_service,
    ):
        pid1 = 'abc-123'
        pid2 = 'def-456'
        mock_resource_likes_service.get_package_like_count_bulk.return_value = {
            pid1: 1,
            pid2: 2,
        }
        mock_download_summary_service.get_package_downloads_bulk.return_value = {
            pid1: 3,
            pid2: 4,
        }
        mock_utilization_summary_service.get_package_utilizations_bulk.return_value = {
            pid1: 0,
            pid2: 0,
        }
        issue_resolutions_bulk = (
            mock_utilization_summary_service.get_package_issue_resolutions_bulk
        )
        issue_resolutions_bulk.return_value = {pid1: 0, pid2: 0}
        mock_resource_summary_service.get_package_comments_bulk.return_value = {
            pid1: 0,
            pid2: 0,
        }
        mock_resource_summary_service.get_package_rating_bulk.return_value = {
            pid1: 0,
            pid2: 0,
        }

        result = get_package_feedback_stats_bulk([{'id': pid1}, None, {'id': pid2}])
        assert set(result.keys()) == {pid1, pid2}
        assert result[pid1]['like_count'] == 1
        assert result[pid2]['like_count'] == 2
