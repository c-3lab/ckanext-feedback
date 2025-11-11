import logging
import os
from typing import Optional

from ckan.common import _, config
from ckan.lib.uploader import Upload, get_uploader
from ckan.plugins import toolkit
from ckan.types import PUploader
from werkzeug.datastructures import FileStorage

log = logging.getLogger(__name__)


DEFAULT_FEEDBACK_STORAGE_PATH = '/var/lib/ckan/feedback'


def get_feedback_storage_path():
    '''Function to get the storage path from config file.'''
    storage_path = config.get(
        'ckan.feedback.storage_path', DEFAULT_FEEDBACK_STORAGE_PATH
    )

    return storage_path


def upload_image_with_validation(image: FileStorage, upload_destination: str) -> str:
    """
    Upload an image file with validation.

    This is a common function used by both resource and utilization controllers
    to validate and upload image files.

    Args:
        image: FileStorage object containing the uploaded image
        upload_destination: Destination path for upload (from get_upload_destination())

    Returns:
        str: Filename of the uploaded image

    Raises:
        toolkit.ValidationError: If file extension or mimetype is invalid

    Note:
        This function validates:
        - File extension (png, jpg, jpeg, gif, webp)
        - MIME type (image/png, image/jpeg, image/gif, image/webp)
    """
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    allowed_mimetypes = {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}

    if image.filename:
        ext = image.filename.rsplit('.', 1)[-1].lower()
        if ext not in allowed_extensions:
            raise toolkit.ValidationError(
                {
                    _('Image Upload'): [
                        _(
                            'Invalid file extension. '
                            'Allowed: png, jpg, jpeg, gif, webp'
                        )
                    ]
                }
            )

    if image.content_type and image.content_type not in allowed_mimetypes:
        raise toolkit.ValidationError(
            {_('Image Upload'): [_('Invalid file type. Only image files are allowed.')]}
        )

    uploader: PUploader = get_uploader(upload_destination)
    data_dict = {
        "image_upload": image,
    }
    uploader.update_data_dict(data_dict, 'image_url', 'image_upload', 'clear_upload')
    attached_image_filename = data_dict["image_url"]
    uploader.upload()

    return attached_image_filename


class FeedbackUpload(Upload):

    def __init__(self, object_type: str, old_filename: Optional[str] = None):
        super(FeedbackUpload, self).__init__("", old_filename)

        self.object_type = object_type
        self.old_filename = old_filename
        self.old_filepath = None

        path = get_feedback_storage_path()
        if not path:
            self.storage_path = None
            return

        self.storage_path = os.path.join(path, object_type)
        if not os.path.isdir(self.storage_path):
            try:
                os.makedirs(self.storage_path)
            except OSError as e:
                # errno 17 is file already exists
                if e.errno != 17:
                    raise
        if old_filename:
            self.old_filepath = os.path.join(self.storage_path, old_filename)
