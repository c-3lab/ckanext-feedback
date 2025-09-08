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


class MoralCheckAction(enum.Enum):
    CHECK_COMPLETED = 'CheckCompleted'
    PREVIOUS_CONFIRM = 'PreviousConfirm'
    PREVIOUS_SUGGESTION = 'PreviousSuggestion'
    INPUT_SELECTED = 'InputSelected'
    SUGGESTION_SELECTED = 'SuggestionSelected'
