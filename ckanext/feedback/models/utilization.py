import datetime
import enum

import ckan.model.domain_object as domain_object
import ckan.model.meta as meta
from ckan.model.resource import Resource
from sqlalchemy import (
    BOOLEAN,
    TIMESTAMP,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Table,
    Text,
    orm,
)

__all__ = ['utilization', 'utilization_comment', 'utilization_summary']


# Declare the utilization table
utilization = Table(
    'utilization',
    meta.metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column('resource_id', Text, ForeignKey('resource.id'), nullable=False),
    Column('title', Text),
    Column('description', Text),
    Column('created', TIMESTAMP),
    Column('approval', BOOLEAN, default=False),
    Column('approved', TIMESTAMP),
    Column('approval_user_id', Text, ForeignKey('resource_comment.user.id')),
)

# Declare the utilization_comment table
utilization_comment = Table(
    'utilization_comment',
    meta.metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column('utilization_id', Text, ForeignKey('utilization.id'), nullable=False),
    Column(
        'category',
        Enum(
            'Request',
            'Question',
            'Advertise',
            'Thank',
            name='utilization_comment_category',
        ),
        nullable=False,
    ),
    Column('content', Text),
    Column('created', TIMESTAMP),
    Column('approval', BOOLEAN, default=False),
    Column('approved', TIMESTAMP),
    Column('approval_user_id', Text, ForeignKey('user.id')),
)

# Declare the utilization_summary table
utilization_summary = Table(
    'utilization_summary',
    meta.metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column('resource_id', Text, ForeignKey('resource.id'), nullable=False),
    Column('utilization', Integer),
    Column('comment', Integer),
    Column('created', TIMESTAMP),
    Column('updated', TIMESTAMP),
)


class Utilization_comment_category(enum.Enum):
    Request = '要望'
    Question = '問合せ'
    Advertise = '宣伝'
    Thank = '感謝'


class Utilization(domain_object.DomainObject):
    id: str
    resource_id: str
    title: str
    description: str
    created: datetime.datetime
    approval: bool
    approved: datetime.datetime
    approval_user_id: str


class UtilizationComment(domain_object.DomainObject):
    id: str
    utilization_id: str
    category: str
    content: str
    created: datetime.datetime
    approval: bool
    approved: datetime.datetime
    approval_user_id: str


class UtilizationSummary(domain_object.DomainObject):
    id: str
    resource_id: str
    utilization: int
    comment: int
    created: datetime.datetime
    updated: datetime.datetime


meta.mapper(Utilization, utilization, properties={'resource': orm.relation(Resource)})
meta.mapper(UtilizationComment, utilization_comment)
meta.mapper(UtilizationSummary, utilization_summary)
