import enum

from ckan.model import domain_object, meta
from sqlalchemy import (  # type: ignore
    BOOLEAN,
    TIMESTAMP,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Table,
    Text,
)

metadata = meta.metadata


class ResourceCommentCategory(enum.Enum):
    request = 'Request'
    question = 'Question'
    advertise = 'Advertise'
    thank = 'Thank'


resource_comment = Table(
    'resource_comment',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column(
        'resource_id',
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
    Column('category', Enum(ResourceCommentCategory), nullable=False),
    Column('content', Text),
    Column('rating', Integer),
    Column('created', TIMESTAMP),
    Column('approval', BOOLEAN, default=False),
    Column('approved', TIMESTAMP),
    Column(
        'approval_user_id',
        Text,
        ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL'),
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
        ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL'),
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


class ResourceComment(domain_object.DomainObject):
    def __init__(
        self,
        id,
        resource_id,
        category,
        content,
        rating,
        created,
        approval,
        approved,
        approval_user_id,
    ):
        self.id = id
        self.resource_id = resource_id
        self.category = category
        self.content = content
        self.rating = rating
        self.created = created
        self.approval = approval
        self.approved = approved
        self.approval_user_id = approval_user_id


class ResourceCommentReply(domain_object.DomainObject):
    def __init__(self, id, resource_comment_id, content, created, creator_user_id):
        self.id = id
        self.resource_comment_id = resource_comment_id
        self.content = content
        self.created = created
        self.creator_user_id = creator_user_id


class ResourceCommentSummary(domain_object.DomainObject):
    def __init__(self, id, resource_id, comment, rating, created, updated):
        self.id = id
        self.resource_id = resource_id
        self.comment = comment
        self.rating = rating
        self.created = created
        self.updated = updated


meta.mapper(ResourceComment, resource_comment)
meta.mapper(ResourceCommentReply, resource_comment_reply)
meta.mapper(ResourceCommentSummary, resource_comment_summary)
