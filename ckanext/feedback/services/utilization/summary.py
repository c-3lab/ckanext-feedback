import logging
from datetime import datetime

from ckan.model import Resource
from sqlalchemy import func

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
    summary = (
        session.query(UtilizationSummary)
        .filter(UtilizationSummary.resource_id == resource_id)
        .first()
    )
    if summary is None:
        summary = UtilizationSummary(
            resource_id=resource_id,
        )
        session.add(summary)


# Recalculate approved utilization related to the utilization summary
def refresh_utilization_summary(resource_id):
    count = (
        session.query(Utilization)
        .filter(
            Utilization.resource_id == resource_id,
            Utilization.approval,
        )
        .count()
    )
    summary = (
        session.query(UtilizationSummary)
        .filter(UtilizationSummary.resource_id == resource_id)
        .first()
    )
    if summary is None:
        summary = UtilizationSummary(
            resource_id=resource_id,
            utilization=count,
        )
        session.add(summary)
    else:
        summary.utilization = count
        summary.updated = datetime.now()


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
    issue_resolution_summary = (
        session.query(IssueResolutionSummary)
        .filter(IssueResolutionSummary.utilization_id == utilization_id)
        .first()
    )
    if issue_resolution_summary is None:
        issue_resolution_summary = IssueResolutionSummary(
            utilization_id=utilization_id,
            issue_resolution=1,
        )
        session.add(issue_resolution_summary)
    else:
        issue_resolution_summary.issue_resolution = (
            issue_resolution_summary.issue_resolution + 1
        )
        issue_resolution_summary.updated = datetime.now()
