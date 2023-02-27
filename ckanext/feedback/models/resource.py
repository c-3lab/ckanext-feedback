import enum
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    ForeignKey,
    Integer,
    Text,
    BOOLEAN,
    TIMESTAMP,
    Enum,
)

metadata = MetaData()


class ResourceCommentCategory(enum.Enum):
    request = 'Request'
    question = 'Question'
    advertise = 'Advertise'
    thank = 'Thank'


resource_comment = Table(
    'resource_comment',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column('resource_id', Text, nullable=False),
    Column('category', Enum(ResourceCommentCategory), nullable=False),
    Column('content', Text),
    Column('rating', Integer),
    Column('created', TIMESTAMP),
    Column('approval', BOOLEAN, default=False),
    Column('approved', TIMESTAMP),
    Column(
        'approval_user_id',
        Text,
        ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'),
    ),
)

resource_comment_reply = Table(
    'resource_comment_reply',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column(
        'resource_comment_id',
        Text,
        ForeignKey('resource_comment.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
    Column('content', Text),
    Column('created', TIMESTAMP),
    Column(
        'creator_user_id',
        Text,
        ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'),
    ),
)

resource_comment_summary = Table(
    'resource_comment_summary',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column(
        'resource_id',
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
    Column('comment', Integer),
    Column('rating', Integer),
    Column('created', TIMESTAMP),
    Column('updated', TIMESTAMP),
)
