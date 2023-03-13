import uuid
from datetime import datetime

from ckan.model.package import Package
from ckan.model.resource import Resource

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization, UtilizationSummary


# Get details from the Resource record
def get_resource_details(resource_id):
    return (
        session.query(
            Resource.name.label('resource_name'),
            Resource.id.label('resource_id'),
            Package.name.label('package_name'),
        )
        .join(Package, Package.id == Resource.package_id)
        .filter(Resource.id == resource_id)
        .one()
    )


# Create new utilization
def create_utilization(resource_id, title, content):
    utilization_id = str(uuid.uuid4())

    utilization = Utilization(
        id=utilization_id,
        resource_id=resource_id,
        title=title,
        description=content,
        created=datetime.now(),
    )
    session.add(utilization)
    return utilization_id


# Create new utilizaton summary
def create_utilization_summary(resource_id):
    summary = session.query(UtilizationSummary).get(resource_id)
    if summary is None:
        summary = UtilizationSummary(
            id=str(uuid.uuid4()),
            resource_id=resource_id,
            utilization=1,
            comment=0,
            created=datetime.now(),
        )
        session.add(summary)
    else:
        summary.utilization = summary.utilization + 1
        summary.updated = datetime.now()
