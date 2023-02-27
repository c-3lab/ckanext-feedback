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


class UtilizationCommentCategory(enum.Enum):
    request = 'Request'
    question = 'Question'
    advertise = 'Advertise'
    thank = 'Thank'


utilization = Table(
    'utilization',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column(
        'resource_id',
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
    Column('title', Text),
    Column('description', Text),
    Column('created', TIMESTAMP),
    Column('approval', BOOLEAN, default=False),
    Column('approved', TIMESTAMP),
    Column(
        'approval_user_id',
        Text,
        ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'),
    ),
)

utilization_comment = Table(
    'utilization_comment',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column(
        'utilization_id',
        Text,
        ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
    Column('category', Enum(UtilizationCommentCategory), nullable=False),
    Column('content', Text),
    Column('created', TIMESTAMP),
    Column('approval', BOOLEAN, default=False),
    Column('approved', TIMESTAMP),
    Column(
        'approval_user_id',
        Text,
        ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'),
    ),
)

issue_resolution = Table(
    'issue_resolution',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column(
        'utilization_id',
        Text,
        ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
    Column('description', Text),
    Column('created', TIMESTAMP),
    Column(
        'creator_user_id',
        Text,
        ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'),
    ),
)

issue_resolution_summary = Table(
    'issue_resolution_summary',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column(
        'utilization_id',
        Text,
        ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
    Column('issue_resolution', Integer),
    Column('created', TIMESTAMP),
    Column('updated', TIMESTAMP),
)

utilization_summary = Table(
    'utilization_summary',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column(
        'resource_id',
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
    Column('utilization', Integer),
    Column('comment', Integer),
    Column('created', TIMESTAMP),
    Column('updated', TIMESTAMP),
)
