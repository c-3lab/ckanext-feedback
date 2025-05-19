import unittest
from unittest.mock import patch

from ckanext.feedback.services.common.upload import (
    FeedbackUpload,
    get_feedback_storage_path,
)


class TestUpload(unittest.TestCase):

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

    @patch('ckanext.feedback.services.common.upload.Upload.__init__')
    @patch('ckanext.feedback.services.common.upload.get_feedback_storage_path')
    @patch('ckanext.feedback.services.common.upload.os.path.isdir')
    @patch('ckanext.feedback.services.common.upload.os.makedirs')
    def test_FeedbackUpload_initializes_when_directory_exists(
        self,
        mock_makedirs,
        mock_isdir,
        mock_get_feedback_storage_path,
        mock_upload_init,
    ):
        mock_upload_init.return_value = None
        mock_get_feedback_storage_path.return_value = '/test/storage_path'
        mock_isdir.return_value = True

        upload = FeedbackUpload(object_type='resource', old_filename='image.png')

        self.assertEqual(upload.storage_path, '/test/storage_path/resource')
        self.assertEqual(upload.object_type, 'resource')
        self.assertEqual(upload.old_filename, 'image.png')
        self.assertEqual(upload.old_filepath, '/test/storage_path/resource/image.png')

        mock_get_feedback_storage_path.assert_called_once_with()
        mock_isdir.assert_called_once_with('/test/storage_path/resource')
        mock_makedirs.assert_not_called()

    @patch('ckanext.feedback.services.common.upload.Upload.__init__')
    @patch('ckanext.feedback.services.common.upload.get_feedback_storage_path')
    @patch('ckanext.feedback.services.common.upload.os.path.isdir')
    @patch('ckanext.feedback.services.common.upload.os.makedirs')
    def test_FeedbackUpload_initializes_without_old_filename(
        self,
        mock_makedirs,
        mock_isdir,
        mock_get_feedback_storage_path,
        mock_upload_init,
    ):
        mock_upload_init.return_value = None
        mock_get_feedback_storage_path.return_value = '/test/storage_path'
        mock_isdir.return_value = True

        upload = FeedbackUpload(object_type='resource', old_filename=None)

        self.assertEqual(upload.storage_path, '/test/storage_path/resource')
        self.assertEqual(upload.object_type, 'resource')
        self.assertIsNone(upload.old_filename)
        self.assertIsNone(upload.old_filepath)

        mock_get_feedback_storage_path.assert_called_once_with()
        mock_isdir.assert_called_once_with('/test/storage_path/resource')
        mock_makedirs.assert_not_called()

    @patch('ckanext.feedback.services.common.upload.Upload.__init__')
    @patch('ckanext.feedback.services.common.upload.get_feedback_storage_path')
    @patch('ckanext.feedback.services.common.upload.os.path.isdir')
    @patch('ckanext.feedback.services.common.upload.os.makedirs')
    def test_FeedbackUpload_creates_directory_when_missing(
        self,
        mock_makedirs,
        mock_isdir,
        mock_get_feedback_storage_path,
        mock_upload_init,
    ):
        mock_upload_init.return_value = None
        mock_get_feedback_storage_path.return_value = '/test/storage_path'
        mock_isdir.return_value = False

        upload = FeedbackUpload(object_type='resource', old_filename='image.png')

        self.assertEqual(upload.storage_path, '/test/storage_path/resource')
        self.assertEqual(upload.object_type, 'resource')
        self.assertEqual(upload.old_filename, 'image.png')
        self.assertEqual(upload.old_filepath, '/test/storage_path/resource/image.png')

        mock_get_feedback_storage_path.assert_called_once_with()
        mock_isdir.assert_called_once_with('/test/storage_path/resource')
        mock_makedirs.assert_called_once_with('/test/storage_path/resource')

    @patch('ckanext.feedback.services.common.upload.Upload.__init__')
    @patch('ckanext.feedback.services.common.upload.get_feedback_storage_path')
    @patch('ckanext.feedback.services.common.upload.os.path.isdir')
    @patch('ckanext.feedback.services.common.upload.os.makedirs')
    def test_FeedbackUpload_handles_eexist_oserror_from_makedirs(
        self,
        mock_makedirs,
        mock_isdir,
        mock_get_feedback_storage_path,
        mock_upload_init,
    ):
        mock_upload_init.return_value = None
        mock_get_feedback_storage_path.return_value = '/test/storage_path'
        mock_isdir.return_value = False
        mock_makedirs.side_effect = OSError(17, 'File exists')

        upload = FeedbackUpload(object_type='resource', old_filename='image.png')

        self.assertEqual(upload.storage_path, '/test/storage_path/resource')
        self.assertEqual(upload.object_type, 'resource')
        self.assertEqual(upload.old_filename, 'image.png')
        self.assertEqual(upload.old_filepath, '/test/storage_path/resource/image.png')

        mock_get_feedback_storage_path.assert_called_once_with()
        mock_isdir.assert_called_once_with('/test/storage_path/resource')
        mock_makedirs.assert_called_once_with('/test/storage_path/resource')

    @patch('ckanext.feedback.services.common.upload.Upload.__init__')
    @patch('ckanext.feedback.services.common.upload.get_feedback_storage_path')
    @patch('ckanext.feedback.services.common.upload.os.path.isdir')
    @patch('ckanext.feedback.services.common.upload.os.makedirs')
    def test_FeedbackUpload_raises_on_permission_error_from_makedirs(
        self,
        mock_makedirs,
        mock_isdir,
        mock_get_feedback_storage_path,
        mock_upload_init,
    ):
        mock_upload_init.return_value = None
        mock_get_feedback_storage_path.return_value = '/test/storage_path'
        mock_isdir.return_value = False
        mock_makedirs.side_effect = OSError(13, 'Permission denied')

        with self.assertRaises(OSError) as cm:
            FeedbackUpload(object_type='resource', old_filename='image.png')

        self.assertEqual(cm.exception.errno, 13)

        mock_get_feedback_storage_path.assert_called_once_with()
        mock_isdir.assert_called_once_with('/test/storage_path/resource')
        mock_makedirs.assert_called_once_with('/test/storage_path/resource')

    @patch('ckanext.feedback.services.common.upload.Upload.__init__')
    @patch('ckanext.feedback.services.common.upload.get_feedback_storage_path')
    @patch('ckanext.feedback.services.common.upload.os.path.isdir')
    @patch('ckanext.feedback.services.common.upload.os.makedirs')
    def test_FeedbackUpload_skips_initialization_when_no_storage_path(
        self,
        mock_makedirs,
        mock_isdir,
        mock_get_feedback_storage_path,
        mock_upload_init,
    ):
        mock_upload_init.return_value = None
        mock_get_feedback_storage_path.return_value = None

        upload = FeedbackUpload(object_type='resource', old_filename='image.png')

        self.assertEqual(upload.storage_path, None)
        self.assertEqual(upload.object_type, 'resource')
        self.assertEqual(upload.old_filename, 'image.png')
        self.assertIsNone(upload.old_filepath)

        mock_get_feedback_storage_path.assert_called_once_with()
        mock_isdir.assert_not_called()
        mock_makedirs.assert_not_called()
