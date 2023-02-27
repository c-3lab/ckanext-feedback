import datetime

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

__all__ = ['resource_comment', 'resource_comment_reply', 'resource_comment_summary']

# Declare the resource_comment table
resource_comment = Table(
    'resource_comment',
    meta.metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column('resource_id', Text, ForeignKey('resource.id'), nullable=False),
    Column('category', Enum('承認待ち', '承認済', name='category_enum'), nullable=False),
    Column('content', Text),
    Column('rating', Integer),
    Column('created', TIMESTAMP),
    Column('approval', BOOLEAN, default=False),
    Column('approved', TIMESTAMP),
    Column('approval_user_id', Text, ForeignKey('user.id')),
)

# Declare the resource_comment_reply table
resource_comment_reply = Table(
    'resource_comment_reply',
    meta.metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column(
        'resource_comment_id', Text, ForeignKey('resource_comment.id'), nullable=False
    ),
    Column('content', Text),
    Column('created', TIMESTAMP),
    Column('creator_user_id', Text, ForeignKey('user.id')),
)

# Declare the resource_comment_summary table
resource_comment_summary = Table(
    'resource_comment_summary',
    meta.metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column('resource_id', Text, ForeignKey('resource.id'), nullable=False),
    Column('comment', Integer),
    Column('rating', Integer),
    Column('created', TIMESTAMP),
    Column('updated', TIMESTAMP),
)


class ResourceComment(domain_object.DomainObject):
    id: str
    resource_id: str
    category: Enum
    content: str
    rating: int
    created: datetime.datetime
    approval: bool
    approved: datetime.datetime
    approval_user_id: str


class ResourceCommentReply(domain_object.DomainObject):
    id: str
    resource_comment_id: str
    content: str
    created: datetime.datetime
    creator_user_id: str


class ResourceCommentSummary(domain_object.DomainObject):
    id: str
    resource_id: str
    comment: int
    rating: int
    created: datetime.datetime
    updated: datetime.datetime


meta.mapper(ResourceComment, resource_comment)
meta.mapper(ResourceCommentReply, resource_comment_reply)
meta.mapper(ResourceCommentSummary, resource_comment_summary)
