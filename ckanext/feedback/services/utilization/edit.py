from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationSummary,
)

session = Session()


# Get details from the Resource record
def get_resource_details(resource_id):
    row = (
        session.query(
            Resource.name.label('resource_name'),
            Resource.id.label('resource_id'),
            Package.name.label('package_name'),
        )
        .join(Package, Package.id == Resource.package_id)
        .filter(Resource.id == resource_id)
        .one()
    )
    return row


# Update utilization
def update_utilization(utilization_id, title, description):
    try:
        session.execute(
            update(Utilization)
            .where(Utilization.id == utilization_id)
            .values(
                title=title,
                description=description,
            )
        )
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


# Delete utilization and related data then update utilization summary
def delete_utilization(utilization_id, resource_id):
    comment_count = (
        session.query(UtilizationComment)
        .filter(UtilizationComment.utilization_id == utilization_id)
        .count()
    )
    print(comment_count)
    try:
        session.execute(
            delete(UtilizationComment).where(
                UtilizationComment.utilization_id == utilization_id
            )
        )
        session.execute(delete(Utilization).where(Utilization.id == utilization_id))
        session.execute(
            update(UtilizationSummary)
            .where(UtilizationSummary.resource_id == resource_id)
            .values(
                utilization=UtilizationSummary.utilization - 1,
                comment=UtilizationSummary.comment - comment_count,
            )
        )
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
