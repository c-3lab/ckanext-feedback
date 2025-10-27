from unittest.mock import patch

import pytest
from flask import Flask

from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.models.session import session
from ckanext.feedback.views.datastore_download import (
    get_datastore_download_blueprint,
    intercept_datastore_download,
)


def get_downloads(resource_id):
    """Helper function to get download count for a resource."""
    count = (
        session.query(DownloadSummary.download)
        .filter(DownloadSummary.resource_id == resource_id)
        .scalar()
    )
    return count or 0


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestDatastoreDownload:
    """Tests for DataStore download interception functionality.

    Note: @pytest.mark.db_test is not used here because these tests
    primarily use mocks and don't require database transactions.
    The integration test uses the resource fixture which handles DB setup.
    """

    def setup_method(self, method):
        """Set up Flask app for test request context."""
        self.app = Flask(__name__)

    @pytest.mark.db_test
    @patch('ckanext.feedback.views.datastore_download.session.commit')
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_with_valid_path(
        self, mock_increment_downloads, mock_increment_monthly, mock_commit, resource
    ):
        """Test that valid DataStore download requests increment counters.

        Uses the resource fixture from conftest.py to ensure proper
        database setup and teardown.
        """
        with self.app.test_request_context(
            f'/datastore/dump/{resource["id"]}', method='GET'
        ):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_called_once_with(resource['id'])
            mock_increment_monthly.assert_called_once_with(resource['id'])
            mock_commit.assert_called_once()
            assert result is None

    @patch('ckanext.feedback.views.datastore_download.session.commit')
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_extracts_resource_id(
        self, mock_increment_downloads, mock_increment_monthly, mock_commit
    ):
        """Test that resource ID is correctly extracted from URL path."""
        # Use valid UUID format
        resource_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'

        with self.app.test_request_context(
            f'/datastore/dump/{resource_id}', method='GET'
        ):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_called_once_with(resource_id)
            mock_increment_monthly.assert_called_once_with(resource_id)
            mock_commit.assert_called_once()
            assert result is None

    @patch('ckanext.feedback.views.datastore_download.session.commit')
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_with_query_params(
        self, mock_increment_downloads, mock_increment_monthly, mock_commit
    ):
        """Test that query parameters don't interfere with resource ID extraction."""
        # Use valid UUID format
        resource_id = 'b2c3d4e5-f678-9012-bcde-f12345678901'

        with self.app.test_request_context(
            f'/datastore/dump/{resource_id}?format=csv', method='GET'
        ):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_called_once_with(resource_id)
            mock_increment_monthly.assert_called_once_with(resource_id)
            mock_commit.assert_called_once()
            assert result is None

    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_ignores_non_datastore_request(
        self, mock_increment_downloads, mock_increment_monthly
    ):
        """Test that non-DataStore paths are ignored."""
        with self.app.test_request_context('/other/path', method='GET'):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_not_called()
            mock_increment_monthly.assert_not_called()
            assert result is None

    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_no_resource_id_match(
        self, mock_increment_downloads, mock_increment_monthly
    ):
        """Test that paths without resource ID don't trigger counting."""
        with self.app.test_request_context('/datastore/dump/', method='GET'):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_not_called()
            mock_increment_monthly.assert_not_called()
            assert result is None

    def test_get_datastore_download_blueprint(self):
        """Test that the blueprint is properly configured."""
        blueprint = get_datastore_download_blueprint()

        assert blueprint is not None
        assert blueprint.name == 'feedback_datastore_override'
        assert blueprint.url_prefix == ''

    @pytest.mark.db_test
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_integration(
        self, mock_increment_downloads, mock_increment_monthly, resource
    ):
        """Integration test using the resource fixture.

        This test ensures proper database setup and uses the resource
        fixture from conftest.py for better test isolation.
        """
        initial_count = get_downloads(resource['id'])
        assert initial_count == 0

        with self.app.test_request_context(
            f'/datastore/dump/{resource["id"]}', method='GET'
        ):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_called_once_with(resource['id'])
            mock_increment_monthly.assert_called_once_with(resource['id'])
            assert result is None

    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_handles_post_request(
        self, mock_increment_downloads, mock_increment_monthly
    ):
        """Test that POST requests don't trigger download counting."""
        resource_id = 'd4e5f678-9012-3456-def0-123456789012'

        with self.app.test_request_context(
            f'/datastore/dump/{resource_id}', method='POST'
        ):
            result = intercept_datastore_download()

            # POST requests should not increment counters
            mock_increment_downloads.assert_not_called()
            mock_increment_monthly.assert_not_called()
            assert result is None

    @patch('ckanext.feedback.views.datastore_download.session.rollback')
    @patch('ckanext.feedback.views.datastore_download.session.commit')
    @patch('ckanext.feedback.views.datastore_download.log')
    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_handles_exception(
        self,
        mock_increment_downloads,
        mock_increment_monthly,
        mock_log,
        mock_commit,
        mock_rollback,
    ):
        """Test that exceptions during counting are handled gracefully."""
        # Use valid UUID format
        resource_id = 'c3d4e5f6-7890-1234-cdef-123456789012'
        mock_increment_downloads.side_effect = Exception('Test error')

        with self.app.test_request_context(
            f'/datastore/dump/{resource_id}', method='GET'
        ):
            result = intercept_datastore_download()

            mock_increment_downloads.assert_called_once_with(resource_id)
            mock_rollback.assert_called_once()
            assert mock_log.warning.call_count == 2
            assert result is None

    @patch(
        'ckanext.feedback.views.datastore_download.increment_resource_downloads_monthly'
    )
    @patch('ckanext.feedback.views.datastore_download.increment_resource_downloads')
    def test_intercept_datastore_download_rejects_invalid_uuid(
        self, mock_increment_downloads, mock_increment_monthly
    ):
        """Test that non-UUID resource IDs are rejected for security"""
        invalid_ids = [
            'test-resource-123',  # Not a UUID
            '../etc/passwd',  # Path traversal attempt
            '<script>alert(1)</script>',  # XSS attempt
            'invalid',  # Too short
        ]

        for invalid_id in invalid_ids:
            with self.app.test_request_context(
                f'/datastore/dump/{invalid_id}', method='GET'
            ):
                result = intercept_datastore_download()

                # Should not increment for invalid IDs
                mock_increment_downloads.assert_not_called()
                mock_increment_monthly.assert_not_called()
                assert result is None

            # Reset mocks for next iteration
            mock_increment_downloads.reset_mock()
            mock_increment_monthly.reset_mock()
