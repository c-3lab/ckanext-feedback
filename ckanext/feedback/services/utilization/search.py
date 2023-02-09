from ckan.common import request
from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy.orm import Session  # type: ignore

from ckanext.feedback.models.utilization import Utilization

session = Session()


# Get the count of records in the Utilization table
def get_data_count():
    count = 0
    keyword = request.args.get("keyword")
    if keyword:
        rows = (
            session.query(Utilization)
            .filter(Utilization.title.like(f"%{keyword}%"))
            .all()
        )
    else:
        rows = session.query(Utilization).all()
    for row in rows:
        count = count + 1
    return count


# Get data from the Utilization table
def get_data():
    keyword = request.args.get("keyword")
    if keyword:
        rows = (
            session.query(Utilization)
            .filter(Utilization.title.like(f"%{keyword}%"))
            .all()
        )
    else:
        rows = session.query(Utilization).all()

    return rows


# If "keyword" exists show it in the search box upon page load
def keep_keyword():
    if request.args.get("keyword"):
        return request.args.get("keyword")
    else:
        return ""


# Get the resource item's package info
def get_package_info(resource_id):
    package_id = (
        session.query(Resource.package_id)
        .filter_by(id=resource_id).scalar()
    )
    package_info = session.query(Package).filter_by(id=package_id).scalar()
    return package_info


# Get the resource item's info
def get_resource_info(resource_id):
    resource_info = session.query(Resource).filter_by(id=resource_id).scalar()
    return resource_info