from ckan.model.user import User
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from ckanext.feedback.models.session import Base


class IssueResolution(Base):
    __tablename__ = 'issue_resolution'
    id = Column(Text, primary_key=True, nullable=False)
    utilization_id = Column(
        Text,
        ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    description = Column(Text)
    created = Column(TIMESTAMP)
    creator_user_id = Column(
        Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')
    )

    utilization = relationship('Utilization', back_populates='issue_resolutions')
    creator_user = relationship(User)


class IssueResolutionSummary(Base):
    __tablename__ = 'issue_resolution_summary'
    id = Column(Text, primary_key=True, nullable=False)
    utilization_id = Column(
        Text,
        ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    issue_resolution = Column(Integer)
    created = Column(TIMESTAMP)
    updated = Column(TIMESTAMP)

    utilization = relationship('Utilization', back_populates='issue_resolution_summary')
