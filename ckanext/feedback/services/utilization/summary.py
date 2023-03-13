from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy.orm import Session

from ckanext.feedback.models.utilization import UtilizationSummary

session = Session()


# Get utilization summary of the target resource
def get_resource_utilization_summary(id):
    count = 0
    rows = (
        session.query(UtilizationSummary.utilization)
        .filter(UtilizationSummary.resource_id == id)
        .all()
    )
    for row in rows:
        count = count + row.utilization

    return count


# Get utilization summary of the target package
def get_package_utilization_summary(id):
    count = 0
    rows = (
        session.query(UtilizationSummary.utilization)
        .join(Resource, Resource.id == UtilizationSummary.resource_id)
        .join(Package, Package.id == Resource.package_id)
        .filter(Package.id == id)
        .all()
    )
    for row in rows:
        count = count + row.utilization

    return count
