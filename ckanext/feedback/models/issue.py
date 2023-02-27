import datetime

from ckan.model import domain_object, meta
from sqlalchemy import (  # type: ignore
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    Table,
    Text,
)

__all__ = ['issue_resolution', 'issue_resolution_summary']

# Declare the issue_resolution table
issue_resolution = Table(
    'issue_resolution',
    meta.metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column('utilization_id', Text, ForeignKey('utilization.id'), nullable=False),
    Column('description', Text),
    Column('created', TIMESTAMP),
    Column('creator_user_id', Text, ForeignKey('user.id')),
)

# Declare the issue_resolution_summary table
issue_resolution_summary = Table(
    'issue_resolution_summary',
    meta.metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column('utilization_id', Text, ForeignKey('utilization.id'), nullable=False),
    Column('issue_resolution', Integer),
    Column('created', TIMESTAMP),
    Column('updated', TIMESTAMP),
)


class IssueResolution(domain_object.DomainObject):
    id: str
    utilization_id: str
    issue_resolution: int
    created: datetime.datetime
    updated: datetime.datetime


class IssueResolutionSummary(domain_object.DomainObject):
    id: str
    utilization_id: str
    issue_resolution: int
    created: datetime.datetime
    updated: datetime.datetime


meta.mapper(IssueResolution, issue_resolution)
meta.mapper(IssueResolutionSummary, issue_resolution_summary)
