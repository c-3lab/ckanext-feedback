import unittest
from unittest.mock import MagicMock, patch

import pytest
from ckan.common import config
from ckan.plugins import toolkit

from ckanext.feedback.services.common.upload import (
    FeedbackUpload,
    get_feedback_storage_path,
    upload_image_with_validation,
)


class TestUpload(unittest.TestCase):

    def test_get_feedback_storage_path(self):
        config['ckan.feedback.storage_path'] = '/test/upload/path'

        storage_path = get_feedback_storage_path()

        assert storage_path == '/test/upload/path'

        config.pop('ckan.feedback.storage_path', None)

    def test_get_feedback_storage_path_no_config(self):
        config.pop('ckan.feedback.storage_path', None)

        storage_path = get_feedback_storage_path()

        assert storage_path == '/var/lib/ckan/feedback'

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


class TestUploadImageWithValidation(unittest.TestCase):
    """Tests for the common upload_image_with_validation function"""

    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_with_valid_file(self, mock_get_uploader):
        """Test successful image upload with valid extension and mimetype"""
        mock_image = MagicMock()
        mock_image.filename = 'test.png'
        mock_image.content_type = 'image/png'

        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = 'uploaded_test.png'

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        result = upload_image_with_validation(mock_image, '/test/upload/path')

        assert result == 'uploaded_test.png'
        mock_get_uploader.assert_called_once_with('/test/upload/path')
        mock_uploader.upload.assert_called_once()

    def test_upload_image_with_invalid_extension(self):
        """Test that invalid file extension raises ValidationError"""
        mock_image = MagicMock()
        mock_image.filename = 'malware.exe'
        mock_image.content_type = 'application/x-msdownload'

        with pytest.raises(toolkit.ValidationError) as exc_info:
            upload_image_with_validation(mock_image, '/test/upload/path')

        assert 'Image Upload' in str(exc_info.value)
        assert 'Invalid file extension' in str(exc_info.value)

    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_with_invalid_mimetype(self, mock_get_uploader):
        """Test that invalid MIME type raises ValidationError"""
        mock_image = MagicMock()
        mock_image.filename = 'test.png'  # Valid extension
        mock_image.content_type = 'application/pdf'  # Invalid mimetype

        with pytest.raises(toolkit.ValidationError) as exc_info:
            upload_image_with_validation(mock_image, '/test/upload/path')

        assert 'Image Upload' in str(exc_info.value)
        assert 'Invalid file type' in str(exc_info.value)
        mock_get_uploader.assert_not_called()

    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_without_filename(self, mock_get_uploader):
        """Test upload with no filename (skips extension validation)"""
        mock_image = MagicMock()
        mock_image.filename = None
        mock_image.content_type = 'image/jpeg'

        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = 'generated_filename.jpg'

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        result = upload_image_with_validation(mock_image, '/test/upload/path')

        assert result == 'generated_filename.jpg'
        mock_get_uploader.assert_called_once_with('/test/upload/path')
        mock_uploader.upload.assert_called_once()

    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_without_content_type(self, mock_get_uploader):
        """Test upload with no content_type (skips mimetype validation)"""
        mock_image = MagicMock()
        mock_image.filename = 'test.gif'
        mock_image.content_type = None

        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = 'test.gif'

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        result = upload_image_with_validation(mock_image, '/test/upload/path')

        assert result == 'test.gif'
        mock_get_uploader.assert_called_once_with('/test/upload/path')
        mock_uploader.upload.assert_called_once()

    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_with_all_allowed_extensions(self, mock_get_uploader):
        """Test that all allowed extensions work"""
        allowed_extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp']

        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = (
                f'test.{data_dict["image_upload"].filename.split(".")[-1]}'
            )

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        for ext in allowed_extensions:
            mock_image = MagicMock()
            mock_image.filename = f'test.{ext}'
            mock_image.content_type = 'image/png'  # Use valid mimetype

            result = upload_image_with_validation(mock_image, '/test/upload/path')

            assert result == f'test.{ext}'

    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_case_insensitive_extension(self, mock_get_uploader):
        """Test that extension validation is case-insensitive"""
        mock_image = MagicMock()
        mock_image.filename = 'test.PNG'  # Uppercase extension
        mock_image.content_type = 'image/png'

        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = 'test.PNG'

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        result = upload_image_with_validation(mock_image, '/test/upload/path')

        assert result == 'test.PNG'
        mock_get_uploader.assert_called_once_with('/test/upload/path')
        mock_uploader.upload.assert_called_once()
