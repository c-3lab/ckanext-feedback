import enum
import uuid
from datetime import datetime

from ckan.model.resource import Resource
from ckan.model.user import User
from sqlalchemy import BOOLEAN, TIMESTAMP, Column, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from ckanext.feedback.models.session import Base
from ckanext.feedback.models.types import MoralCheckAction


# TODO: Organize and consolidate Enum definitions and sa.Enum wrappers.
# 'https://github.com/c-3lab/ckanext-feedback/issues/286'
class UtilizationCommentCategory(enum.Enum):
    REQUEST = 'Request'
    QUESTION = 'Question'
    THANK = 'Thank'


class Utilization(Base):
    __tablename__ = 'utilization'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    title = Column(Text)
    url = Column(Text)
    description = Column(Text)
    comment = Column(Integer, default=0)
    created = Column(TIMESTAMP, default=datetime.now)
    approval = Column(BOOLEAN, default=False)
    approved = Column(TIMESTAMP)
    approval_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )

    resource = relationship(Resource)
    approval_user = relationship(User)
    comments = relationship(
        'UtilizationComment', back_populates='utilization', cascade='all, delete-orphan'
    )
    issue_resolutions = relationship(
        'IssueResolution', back_populates='utilization', cascade='all, delete-orphan'
    )
    issue_resolution_summary = relationship(
        'IssueResolutionSummary',
        back_populates='utilization',
        cascade='all, delete-orphan',
    )


class UtilizationComment(Base):
    __tablename__ = 'utilization_comment'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    utilization_id = Column(
        Text,
        ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    category = Column(Enum(UtilizationCommentCategory), nullable=False)
    content = Column(Text)
    created = Column(TIMESTAMP, default=datetime.now)
    approval = Column(BOOLEAN, default=False)
    approved = Column(TIMESTAMP)
    approval_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )
    attached_image_filename = Column(Text)

    utilization = relationship('Utilization', back_populates='comments')
    approval_user = relationship(User)


class UtilizationCommentReply(Base):
    __tablename__ = 'utilization_comment_reply'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    utilization_comment_id = Column(
        Text,
        ForeignKey('utilization_comment.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    content = Column(Text)
    created = Column(TIMESTAMP, default=datetime.now)
    approval = Column(BOOLEAN, default=False)
    approved = Column(TIMESTAMP)
    approval_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )
    creator_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )
    attached_image_filename = Column(Text)


class UtilizationSummary(Base):
    __tablename__ = 'utilization_summary'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )
    utilization = Column(Integer, default=0)
    created = Column(TIMESTAMP, default=datetime.now)
    updated = Column(TIMESTAMP)

    resource = relationship(Resource)


class UtilizationCommentMoralCheckLog(Base):
    __tablename__ = 'utilization_comment_moral_check_log'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    utilization_id = Column(
        Text,
        ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    action = Column(Enum(MoralCheckAction, name='utilizationcomment_moralcheckaction'))
    input_comment = Column(Text)
    suggested_comment = Column(Text)
    output_comment = Column(Text)
    timestamp = Column(TIMESTAMP, default=datetime.now)

    utilization = relationship(Utilization)
