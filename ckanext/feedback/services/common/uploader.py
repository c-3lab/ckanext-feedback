from ckan.lib.uploader import Upload


class FeedbackUpload(Upload):

    def __init__(self, upload_to, old_filename=None):
        super(FeedbackUpload, self).__init__(upload_to, old_filename)
