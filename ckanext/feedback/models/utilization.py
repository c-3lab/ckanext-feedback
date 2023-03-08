import enum

from ckan import model
from sqlalchemy import BOOLEAN, TIMESTAMP, Column, Enum, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base(metadata=model.meta.metadata)


class UtilizationCommentCategory(enum.Enum):
    request = 'Request'
    question = 'Question'
    advertise = 'Advertise'
    thank = 'Thank'


class Utilization(Base):
    __tablename__ = 'utilization'
    id = Column(Text, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    title = Column(Text)
    description = Column(Text)
    created = Column(TIMESTAMP)
    approval = Column(BOOLEAN, default=False)
    approved = Column(TIMESTAMP)
    approval_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )


class UtilizationComment(Base):
    __tablename__ = 'utilization_comment'
    id = Column(Text, primary_key=True, nullable=False)
    utilization_id = Column(
        Text,
        ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    category = Column(Enum(UtilizationCommentCategory), nullable=False)
    content = Column(Text)
    created = Column(TIMESTAMP)
    approval = Column(BOOLEAN, default=False)
    approved = Column(TIMESTAMP)
    approval_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )


class UtilizationSummary(Base):
    __tablename__ = 'utilization_summary'
    id = Column(Text, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    utilization = Column(Integer)
    comment = Column(Integer)
    created = Column(TIMESTAMP)
    updated = Column(TIMESTAMP)
