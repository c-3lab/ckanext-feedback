from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from ckanext.feedback.models.utilization import Utilization
from ckanext.feedback.models.issue import IssueResolutionSummary

session = Session()


# Get records from the Utilization table
def get_utilizations(id=None, keyword=None, approval=False):
    query = (
        session.query(
            Utilization.id,
            Utilization.title,
            Utilization.created,
            Utilization.approval,
            Resource.name.label('resource_name'),
            Resource.id.label('resource_id'),
            Package.name.label('package_name'),
            coalesce(IssueResolutionSummary.issue_resolution, 0).label('issue_resolution'),
        )
        .join(Resource, Resource.id == Utilization.resource_id)
        .join(Package, Package.id == Resource.package_id)
        .outerjoin(IssueResolutionSummary, IssueResolutionSummary.utilization_id == Utilization.id)
        .order_by(Utilization.created.desc())
    )
    if id:
        query = query.filter(or_(Resource.id == id, Package.id == id))
    if keyword:
        query = query.filter(
            or_(
                Utilization.title.like(f'%{keyword}%'),
                Resource.name.like(f'%{keyword}%'),
                Package.name.like(f'%{keyword}%'),
            )
        )
    if approval:
        query = query.filter(Utilization.approval == approval)

    return query.all()
