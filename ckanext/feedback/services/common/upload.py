import logging
import os
from typing import Optional

from ckan.common import config
from ckan.lib.uploader import Upload

log = logging.getLogger(__name__)


def get_feedback_storage_path() -> str:
    '''Function to get the storage path from config file.'''
    storage_path = config.get('ckan.feedback.storage_path')
    if not storage_path:
        log.critical(
            'Please specify a ckan.feedback.storage_path'
            'in your config for your uploads'
        )

    return storage_path


class FeedbackUpload(Upload):

    def __init__(self, object_type: str, old_filename: Optional[str] = None):
        super(FeedbackUpload, self).__init__("", old_filename)
        if not self.storage_path:
            return

        path = get_feedback_storage_path()
        if not path:
            self.storage_path = None
            return

        self.storage_path = os.path.join(path, object_type)
        if os.path.isdir(self.storage_path):
            pass
        else:
            try:
                os.makedirs(self.storage_path)
            except OSError as e:
                # errno 17 is file already exists
                if e.errno != 17:
                    raise
        self.object_type = object_type
        self.old_filename = old_filename
        if old_filename:
            self.old_filepath = os.path.join(self.storage_path, old_filename)
