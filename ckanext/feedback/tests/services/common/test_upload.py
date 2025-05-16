from unittest.mock import patch

from ckanext.feedback.services.common.upload import get_feedback_storage_path


class TestUpload:

    @patch('ckanext.feedback.services.common.upload.config')
    def test_get_feedback_storage_path(self, mock_config):
        mock_config.get.return_value = "/fake/storage_path"

        get_feedback_storage_path()

        mock_config.get.assert_called_once_with('ckan.feedback.storage_path')

    @patch('ckanext.feedback.services.common.upload.config')
    @patch('ckanext.feedback.services.common.upload.log')
    def test_get_feedback_storage_path_no_config(self, mock_log, mock_config):
        mock_config.get.return_value = None

        get_feedback_storage_path()

        mock_config.get.assert_called_once_with('ckan.feedback.storage_path')
        mock_log.critical.assert_called_once_with(
            'Please specify a ckan.feedback.storage_path'
            'in your config for your uploads'
        )
