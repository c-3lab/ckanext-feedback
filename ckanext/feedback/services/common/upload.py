from typing import Optional

from ckan.lib.uploader import Upload


class FeedbackUpload(Upload):

    def __init__(self, object_type: str, old_filename: Optional[str] = None):
        super(FeedbackUpload, self).__init__(object_type, old_filename)
