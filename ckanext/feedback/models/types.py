import enum


# TODO: Organize and consolidate Enum definitions and sa.Enum wrappers.
# 'https://github.com/c-3lab/ckanext-feedback/issues/286'
class CommentCategory(enum.Enum):
    REQUEST = 'Request'
    QUESTION = 'Question'
    THANK = 'Thank'
