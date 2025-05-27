import logging
import os
from typing import Optional

from ckan.common import config
from ckan.lib.uploader import Upload

log = logging.getLogger(__name__)


def get_feedback_storage_path():
    '''Function to get the storage path from config file.'''
    default_feedback_storage_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..')
    )

    storage_path = config.get(
        'ckan.feedback.storage_path', default_feedback_storage_path
    )

    return storage_path


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
