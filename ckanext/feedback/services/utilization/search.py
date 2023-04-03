from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import func, or_

from ckanext.feedback.models.issue import IssueResolutionSummary
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization


# Get records from the Utilization table
def get_utilizations(id=None, keyword=None, approval=None):
    query = (
        session.query(
            Utilization.id,
            Utilization.title,
            Utilization.comment,
            Utilization.created,
            Utilization.approval,
            Resource.name.label('resource_name'),
            Resource.id.label('resource_id'),
            Package.name.label('package_name'),
            func.coalesce(IssueResolutionSummary.issue_resolution, 0).label(
                'issue_resolution'
            ),
        )
        .join(Resource, Utilization.resource)
        .join(Package)
        .outerjoin(IssueResolutionSummary)
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
    if approval is not None:
        query = query.filter(Utilization.approval == approval)

    return query.all()
