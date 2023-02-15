from ckan.common import request
from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import or_  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from ckanext.feedback.models.utilization import Utilization

session = Session()


# Get data from the Utilization table
def get_data():
    rows = (
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
        )
    keyword = request.args.get("keyword")
    if keyword:
        rows = (
            rows.filter(
                or_(
                    Utilization.title.like(f'%{keyword}%'),
                    Resource.name.like(f'%{keyword}%'),
                    Package.name.like(f'%{keyword}%')
                )
            )
        )
    rows = rows.all()

    return rows


# If "keyword" exists show it in the search box upon page load
def keep_keyword():
    if request.args.get("keyword"):
        return request.args.get("keyword")
    else:
        return ""
