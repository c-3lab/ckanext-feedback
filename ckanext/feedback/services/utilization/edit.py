from ckan.model.package import Package
from ckan.model.resource import Resource

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization


# Get details from the Utilization record
def get_utilization_details(utilization_id):
    return session.query(Utilization).get(utilization_id)


# Get details from the Resource record
def get_resource_details(resource_id):
    return (
        session.query(
            Resource.name.label('resource_name'),
            Resource.id.label('resource_id'),
            Package.title.label('package_title'),
            Package.name.label('package_name'),
        )
        .join(Package)
        .filter(Resource.id == resource_id)
        .first()
    )


# Update utilization
def update_utilization(utilization_id, title, url, description):
    utilization = session.query(Utilization).get(utilization_id)
    utilization.title = title
    utilization.url = url
    utilization.description = description


# Delete utilization
def delete_utilization(utilization_id):
    utilization = session.query(Utilization).get(utilization_id)
    session.delete(utilization)
