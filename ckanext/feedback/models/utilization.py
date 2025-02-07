import enum
import uuid
from datetime import datetime

from ckan.model.resource import Resource
from ckan.model.user import User
from sqlalchemy import BOOLEAN, TIMESTAMP, Column, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from ckanext.feedback.models.session import Base


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

    utilization = relationship('Utilization', back_populates='comments')
    approval_user = relationship(User)


class UtilizationSummary(Base):
    __tablename__ = 'utilization_summary'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    utilization = Column(Integer, default=0)
    created = Column(TIMESTAMP, default=datetime.now)
    updated = Column(TIMESTAMP)

    resource = relationship(Resource)
