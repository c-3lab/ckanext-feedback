import enum

from ckan.model import domain_object, meta
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

metadata = meta.metadata


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
        ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL'),
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
        ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL'),
    ),
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


class Utilization(domain_object.DomainObject):
    def __init__(
        self,
        id,
        resource_id,
        title,
        description,
        created,
        approval,
        approved,
        approval_user_id,
    ):
        self.id = id
        self.resource_id = resource_id
        self.title = title
        self.description = description
        self.created = created
        self.approval = approval
        self.approved = approved
        self.approval_user_id = approval_user_id


class UtilizationComment(domain_object.DomainObject):
    def __init__(
        self,
        id,
        utilization_id,
        category,
        content,
        created,
        approval,
        approved,
        approval_user_id,
    ):
        self.id = id
        self.utilization_id = utilization_id
        self.category = category
        self.content = content
        self.created = created
        self.approval = approval
        self.approved = approved
        self.approval_user_id = approval_user_id


class UtilizationSummary(domain_object.DomainObject):
    def __init__(self, id, resource_id, utilization, comment, created, updated):
        self.id = id
        self.resource_id = resource_id
        self.utilization = utilization
        self.comment = comment
        self.created = created
        self.updated = updated


meta.mapper(Utilization, utilization, properties={'resource': orm.relation(Resource)})
meta.mapper(UtilizationComment, utilization_comment)
meta.mapper(UtilizationSummary, utilization_summary)
