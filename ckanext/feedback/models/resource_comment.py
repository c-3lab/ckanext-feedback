import enum
import uuid
from datetime import datetime

from ckan.model.resource import Resource
from ckan.model.user import User
from sqlalchemy import (
    BOOLEAN,
    TIMESTAMP,
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship

from ckanext.feedback.models.session import Base


class ResourceCommentCategory(enum.Enum):
    REQUEST = 'Request'
    QUESTION = 'Question'
    THANK = 'Thank'


class ResourceComment(Base):
    __tablename__ = 'resource_comment'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    category = Column(Enum(ResourceCommentCategory))
    content = Column(Text)
    rating = Column(Integer)
    created = Column(TIMESTAMP, default=datetime.now)
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
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    resource_comment_id = Column(
        Text,
        ForeignKey('resource_comment.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    content = Column(Text)
    created = Column(TIMESTAMP, default=datetime.now)
    creator_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )

    resource_comment = relationship('ResourceComment', back_populates='reply')
    creator_user = relationship(User)


class ResourceCommentSummary(Base):
    __tablename__ = 'resource_comment_summary'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    # the total count of all comment
    comment = Column(Integer, default=0)
    # the number of comments that have ratings
    rating_comment = Column(Integer, default=0)
    rating = Column(Float, default=0)
    created = Column(TIMESTAMP, default=datetime.now)
    updated = Column(TIMESTAMP)

    resource = relationship(Resource)
