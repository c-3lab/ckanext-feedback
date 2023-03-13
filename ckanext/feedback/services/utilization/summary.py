import datetime
import logging
import uuid

from ckan.model import Resource
from sqlalchemy import func
from sqlalchemy.orm import Session

from ckanext.feedback.models.issue import IssueResolutionSummary
from ckanext.feedback.models.utilization import Utilization

log = logging.getLogger(__name__)

session = Session()

def get_package_issue_resolutions(package_id):
    count = (
        session.query(func.sum(IssueResolutionSummary.issue_resolution))
        .join(Utilization, Utilization.id == IssueResolutionSummary.utilization_id)
        .join(Resource, Resource.id == Utilization.resource_id)
        .filter(Resource.package_id == package_id)
        .scalar()
    )
    return count or 0

def get_resource_issue_resolutions(resource_id):
    count = (
        session.query(func.sum(IssueResolutionSummary.issue_resolution))
        .join(Utilization, Utilization.id == IssueResolutionSummary.utilization_id)
        .filter(Utilization.resource_id == resource_id)
        .scalar()
    )
    return count or 0