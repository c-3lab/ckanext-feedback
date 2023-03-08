from ckan import model
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base(metadata=model.meta.metadata)


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
