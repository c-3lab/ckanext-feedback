from ckan.model.resource import Resource

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization


# Get resource from the Resource id
def get_resource(resource_id):
    return session.query(Resource).filter(Resource.id == resource_id).first()


# Create new utilization
def create_utilization(resource_id, title, url, description):
    utilization = Utilization(
        resource_id=resource_id,
        title=title,
        url=url,
        description=description,
    )
    session.add(utilization)
    return utilization
