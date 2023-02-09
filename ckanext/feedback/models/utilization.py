from sqlalchemy import *
import ckan.model.meta as meta
import ckan.model.domain_object as domain_object
import datetime

__all__ = ["utilization", "utilization_comment", "utilization_summary"]

# Declare the utilization table
utilization = Table(
    "utilization",
    meta.metadata,
    Column("id", Text, primary_key=True, nullable=False),
    Column("resource_id", Text, ForeignKey("resource_comment.resource_id"), nullable=False),
    Column("title", Text),
    Column("description", Text),
    Column("created", TIMESTAMP),
    Column("approval", BOOLEAN, default=False),
    Column("approved", TIMESTAMP),
    Column("approval_user_id", Text, ForeignKey("resource_comment.approval_user_id"))
)

# Declare the utilization_comment table
utilization_comment = Table(
    "utilization_comment",
    meta.metadata,
    Column("id", Text, primary_key=True, nullable=False),
    Column("utilization_id", Text, ForeignKey("issue_resolution.utilization_id"), nullable=False),
    Column("category", Enum("承認待ち", "承認済", name="category_enum"), nullable=False),
    Column("content", Text),
    Column("created", TIMESTAMP),
    Column("approval", BOOLEAN, default=False),
    Column("approved", TIMESTAMP),
    Column("approval_user_id", Text, ForeignKey("issue_resolution.creator_user_id"), ForeignKey("resource_comment_reply.creator_user_id"))
)

# Declare the utilization_summary table
utilization_summary = Table(
    "utilization_summary",
    meta.metadata,
    Column("id", Text, primary_key=True, nullable=False),
    Column("resource_id", Text, ForeignKey("resource.id"), nullable=False),
    Column("utilization", Integer),
    Column("comment", Integer),
    Column("created", TIMESTAMP),
    Column("updated", TIMESTAMP)
)

class Utilization(domain_object.DomainObject):
    id: str
    resource_id: str
    title: str
    description: str
    created: datetime.datetime
    approval: bool
    approved: datetime.datetime
    approval_user_id: str

class UtilizationComment(domain_object.DomainObject):
    id: str
    utilization_id: str
    category: str
    content: str
    created: datetime.datetime
    approval: bool
    approved: datetime.datetime
    approval_user_id: str

class UtilizationSummary(domain_object.DomainObject):
    id: str
    resource_id: str
    utilization: int
    comment: int
    created: datetime.datetime
    updated: datetime.datetime

meta.mapper(Utilization, utilization)
meta.mapper(UtilizationComment, utilization_comment)
meta.mapper(UtilizationSummary, utilization_summary)
