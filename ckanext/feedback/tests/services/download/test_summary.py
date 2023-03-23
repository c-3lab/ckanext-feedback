from unittest.mock import patch, MagicMock

from ckanext.feedback.services.download.summary import (
    get_package_downloads,
    get_resource_downloads,
    increment_resource_downloads
)


class TestDownloadView:
    @patch('ckanext.feedback.services.download.summary.session.commit')
    @patch('ckanext.feedback.services.download.summary.session.query')
    @patch('ckanext.feedback.services.download.summary.session.add')
    def test_increment_resource_downloads(self,mock_add, mock_query, mock_commit):
        mock_query.return_value.filter.return_value.first.return_value = None
        increment_resource_downloads('resource_id')
        mock_commit.assert_called_once()
        mock_add.assert_called_once()

    @patch('ckanext.feedback.services.download.summary.session.commit')
    @patch('ckanext.feedback.services.download.summary.session.query')
    def test_increment_resource_downloads2(self, mock_query, mock_commit):
        mock_download_summary = MagicMock()
        mock_download_summary.download = 1
        mock_query.return_value.filter.return_value.first.return_value = mock_download_summary
        increment_resource_downloads('resource_id')
        mock_commit.assert_called_once()
        assert mock_download_summary.download == 2

    @patch('ckanext.feedback.services.download.summary.session.query')
    def test_get_package_download(self, mock_query):
        mock_query.return_value.join.return_value.filter.return_value.scalar.return_value = None
        assert get_package_downloads('package_id') == 0
        mock_query.return_value.join.return_value.filter.return_value.scalar.return_value = 1
        assert get_package_downloads('package_id') == 1

    @patch('ckanext.feedback.services.download.summary.session.query')
    def test_get_resource_download(self, mock_query):
        mock_query.return_value.filter.return_value.scalar.return_value = None
        assert get_resource_downloads('resource_id') == 0
        mock_query.return_value.filter.return_value.scalar.return_value = 1
        assert get_resource_downloads('resource_id') == 1
