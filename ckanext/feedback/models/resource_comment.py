import enum

from ckan.model.resource import Resource
from ckan.model.user import User
from sqlalchemy import BOOLEAN, TIMESTAMP, Column, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from ckanext.feedback.models.session import Base


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

    resource = relationship(Resource)
    approval_user = relationship(User)
    reply = relationship('ResourceCommentReply', uselist=False)


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

    resource_comment = relationship('ResourceComment', back_populates='reply')
    creator_user = relationship(User)


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

    resource = relationship(Resource)
