from ckan.model import domain_object, meta
from sqlalchemy import (  # type: ignore
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    Table,
    Text,
)

from ckanext.feedback.models.utilization import metadata

# Declare the issue_resolution table
issue_resolution = Table(
    'issue_resolution',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column('utilization_id', Text, ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
    Column('description', Text),
    Column('created', TIMESTAMP),
    Column('creator_user_id', Text, ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL')),
)

# Declare the issue_resolution_summary table
issue_resolution_summary = Table(
    'issue_resolution_summary',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column('utilization_id', Text, ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
    Column('issue_resolution', Integer),
    Column('created', TIMESTAMP),
    Column('updated', TIMESTAMP),
)


class IssueResolution(domain_object.DomainObject):
    def __init__(self, id, utilization_id, issue_resolution, created, updated):
        self.id = id
        self.utilization_id = utilization_id
        self.issue_resolution = issue_resolution
        self.created = created
        self.updated = updated


class IssueResolutionSummary(domain_object.DomainObject):
    def __init__(self, id, utilization_id, issue_resolution, created, updated):
        self.id = id
        self.utilization_id = utilization_id
        self.issue_resolution = issue_resolution
        self.created = created
        self.updated = updated


meta.mapper(IssueResolution, issue_resolution)
meta.mapper(IssueResolutionSummary, issue_resolution_summary)
