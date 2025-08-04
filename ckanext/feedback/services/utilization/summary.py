import logging
from datetime import datetime

from ckan.model import Resource
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from ckanext.feedback.models.issue import IssueResolutionSummary
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization, UtilizationSummary

log = logging.getLogger(__name__)


# Get utilization summary count of the target package
def get_package_utilizations(package_id):
    count = (
        session.query(func.sum(UtilizationSummary.utilization))
        .join(Resource)
        .filter(
            Resource.package_id == package_id,
            Resource.state == "active",
        )
        .scalar()
    )
    return count or 0


# Get utilization summary count of the target resource
def get_resource_utilizations(resource_id):
    count = (
        session.query(UtilizationSummary.utilization)
        .filter(UtilizationSummary.resource_id == resource_id)
        .scalar()
    )
    return count or 0


# Create new utilizaton summary
def create_utilization_summary(resource_id):
    now = datetime.now()

    insert_summary = insert(UtilizationSummary).values(
        resource_id=resource_id,
        created=now,
    )
    summary = insert_summary.on_conflict_do_nothing(index_elements=['resource_id'])
    session.execute(summary)


# Recalculate approved utilization related to the utilization summary
def refresh_utilization_summary(resource_id):
    now = datetime.now()

    count = (
        session.query(Utilization)
        .filter(
            Utilization.resource_id == resource_id,
            Utilization.approval,
        )
        .count()
    )

    insert_summary = insert(UtilizationSummary).values(
        resource_id=resource_id,
        utilization=count,
        created=now,
        updated=now,
    )
    summary = insert_summary.on_conflict_do_update(
        index_elements=['resource_id'],
        set_={
            'utilization': insert_summary.excluded.utilization,
            'updated': now,
        },
    )
    session.execute(summary)


def get_package_issue_resolutions(package_id):
    count = (
        session.query(func.sum(IssueResolutionSummary.issue_resolution))
        .join(Utilization)
        .join(Resource)
        .filter(
            Resource.package_id == package_id,
            Resource.state == "active",
        )
        .scalar()
    )
    return count or 0


def get_resource_issue_resolutions(resource_id):
    count = (
        session.query(func.sum(IssueResolutionSummary.issue_resolution))
        .join(Utilization)
        .filter(Utilization.resource_id == resource_id)
        .scalar()
    )
    return count or 0


def increment_issue_resolution_summary(utilization_id):
    now = datetime.now()

    insert_issue_resolution_summary = insert(IssueResolutionSummary).values(
        utilization_id=utilization_id,
        issue_resolution=1,
        created=now,
        updated=now,
    )
    issue_resolution_summary = insert_issue_resolution_summary.on_conflict_do_update(
        index_elements=['utilization_id'],
        set_={
            'issue_resolution': IssueResolutionSummary.issue_resolution + 1,
            'updated': now,
        },
    )
    session.execute(issue_resolution_summary)
