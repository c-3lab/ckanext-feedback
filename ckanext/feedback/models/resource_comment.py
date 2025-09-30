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
from ckanext.feedback.models.types import (
    MoralCheckAction,
    ResourceCommentResponseStatus,
)


# TODO: Organize and consolidate Enum definitions and sa.Enum wrappers.
# 'https://github.com/c-3lab/ckanext-feedback/issues/286'
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
    attached_image_filename = Column(Text)

    resource = relationship(Resource)
    approval_user = relationship(User, foreign_keys=[approval_user_id])
    replies = relationship(
        'ResourceCommentReply',
        back_populates='resource_comment',
        uselist=True,
        order_by="ResourceCommentReply.created",
    )
    reactions = relationship(
        'ResourceCommentReactions', back_populates='resource_comment', uselist=False
    )


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

    resource_comment = relationship('ResourceComment', back_populates='replies')
    creator_user = relationship(User, foreign_keys=[creator_user_id])
    approval = Column(BOOLEAN, default=False)
    approved = Column(TIMESTAMP)
    approval_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )
    approval_user = relationship(User, foreign_keys=[approval_user_id])
    attached_image_filename = Column(Text)


class ResourceCommentSummary(Base):
    __tablename__ = 'resource_comment_summary'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )
    # the total count of all comment
    comment = Column(Integer, default=0)
    # the number of comments that have ratings
    rating_comment = Column(Integer, default=0)
    rating = Column(Float, default=0)
    created = Column(TIMESTAMP, default=datetime.now)
    updated = Column(TIMESTAMP)

    resource = relationship(Resource)


class ResourceCommentReactions(Base):
    __tablename__ = 'resource_comment_reactions'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    resource_comment_id = Column(
        Text,
        ForeignKey('resource_comment.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )
    response_status = Column(Enum(ResourceCommentResponseStatus))
    admin_liked = Column(BOOLEAN, default=False)
    created = Column(TIMESTAMP, default=datetime.now)
    updated = Column(TIMESTAMP)
    updater_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )

    resource_comment = relationship('ResourceComment', back_populates='reactions')
    updater_user = relationship(User)


class ResourceCommentMoralCheckLog(Base):
    __tablename__ = 'resource_comment_moral_check_log'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    action = Column(Enum(MoralCheckAction, name='resourcecomment_moralcheckaction'))
    input_comment = Column(Text)
    suggested_comment = Column(Text)
    output_comment = Column(Text)
    timestamp = Column(TIMESTAMP, default=datetime.now)

    resource = relationship(Resource)
