import enum

from ckan import model
from sqlalchemy import BOOLEAN, TIMESTAMP, Column, Enum, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base(metadata=model.meta.metadata)


class ResourceCommentCategory(enum.Enum):
    request = 'Request'
    question = 'Question'
    advertise = 'Advertise'
    thank = 'Thank'


class ResourceComment(Base):
    __tablename__ = 'resource_comment'
    id = Column(Text, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    category = Column(Enum(ResourceCommentCategory), nullable=False)
    content = Column(Text)
    rating = Column(Integer)
    created = Column(TIMESTAMP)
    approval = Column(BOOLEAN, default=False)
    approved = Column(TIMESTAMP)
    approval_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )


class ResourceCommentReply(Base):
    __tablename__ = 'resource_comment_reply'
    id = Column(Text, primary_key=True, nullable=False)
    resource_comment_id = Column(
        Text,
        ForeignKey('resource_comment.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    content = Column(Text)
    created = Column(TIMESTAMP)
    creator_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )


class ResourceCommentSummary(Base):
    __tablename__ = 'resource_comment_summary'
    id = Column(Text, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    comment = Column(Integer)
    rating = Column(Integer)
    created = Column(TIMESTAMP)
    updated = Column(TIMESTAMP)
