from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ckanext.feedback.models.utilization import Utilization

session = Session()


# Get records from the Utilization table
def get_utilizations(keyword):
    rows = (
        session.query(
            Utilization.id,
            Utilization.title,
            Utilization.created,
            Utilization.approval,
            Resource.name.label('resource_name'),
            Resource.id.label('resource_id'),
            Package.name.label('package_name'),
        )
        .join(Resource, Resource.id == Utilization.resource_id)
        .join(Package, Package.id == Resource.package_id)
        .order_by(Utilization.created.desc())
    )
    if keyword:
        rows = rows.filter(
            or_(
                Utilization.title.like(f'%{keyword}%'),
                Resource.name.like(f'%{keyword}%'),
                Package.name.like(f'%{keyword}%'),
            )
        )
    # Set "rows" as the final query results
    rows = rows.all()

    return rows


# Get approved records from the Utilization table
def get_approved_utilizations(keyword):
    rows = (
        session.query(
            Utilization.id,
            Utilization.title,
            Utilization.created,
            Utilization.approval,
            Resource.name.label('resource_name'),
            Resource.id.label('resource_id'),
            Package.name.label('package_name'),
        )
        .join(Resource, Resource.id == Utilization.resource_id)
        .join(Package, Package.id == Resource.package_id)
        .filter(Utilization.approval == 'true')
        .order_by(Utilization.created.desc())
    )
    if keyword:
        rows = rows.filter(
            or_(
                Utilization.title.like(f'%{keyword}%'),
                Resource.name.like(f'%{keyword}%'),
                Package.name.like(f'%{keyword}%'),
            )
        )
    # Set "rows" as the final query results
    rows = rows.all()

    return rows
