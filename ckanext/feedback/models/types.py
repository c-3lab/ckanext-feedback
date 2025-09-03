import enum


# TODO: Organize and consolidate Enum definitions.
# 'https://github.com/c-3lab/ckanext-feedback/issues/286'
class CommentCategory(enum.Enum):
    REQUEST = 'Request'
    QUESTION = 'Question'
    THANK = 'Thank'


class ResourceCommentResponseStatus(enum.Enum):
    STATUS_NONE = 'StatusNone'
    NOT_STARTED = 'NotStarted'
    IN_PROGRESS = 'InProgress'
    COMPLETED = 'Completed'
    REJECTED = 'Rejected'
