from ckanext.feedback.controllers.download import DownloadController
from unittest.mock import patch
from flask import Flask


class TestDownloadController:
    @patch('ckanext.feedback.controllers.download.increment_resource_downloads')
    def test_increment_resource_download(self, mock_increment):
        DownloadController.increment_resource_downloads('resource_id')
        mock_increment.assert_called_once()

    @patch('ckanext.feedback.controllers.download.download')
    @patch('ckanext.feedback.controllers.download.increment_resource_downloads')
    def test_extended_download(self, mock_increment, mock_download):
        self.app = Flask(__name__)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.ctx.pop()
        with self.app.test_request_context(headers={'Sec-Fetch-Dest': 'image'}):
            DownloadController.extended_download('package_type', 'package_id', 'resource_id', None)
            assert mock_download

        with self.app.test_request_context(headers={'Sec-Fetch-Dest': 'document'}):
            DownloadController.extended_download('package_type', 'package_id', 'resource_id', None)
            mock_increment.assert_called_once()
            assert mock_download
            