from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy.orm import Session

from ckanext.feedback.models.utilization import Utilization

session = Session()


# Get details from the Utilization record
def get_utilization_details():
    row = (
        session.query(
            Utilization.title,
            Utilization.created,
            Utilization.approval,
            Resource.name.label('resource_name'),
            Resource.id.label('resource_id'),
            Package.name.label('package_name'),
        )
        .join(Resource, Resource.id == Utilization.resource_id)
        .join(Package, Package.id == Resource.package_id)
        .filter(Utilization.id == '1')
        .one()
    )
    return row
