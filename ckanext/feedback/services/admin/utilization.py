from datetime import datetime

from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import literal

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization, UtilizationComment


def get_utilizations_query(org_list):
    org_names = [org['name'] for org in org_list]

    query = (
        session.query(
            Group.name.label('group_name'),
            Package.name.label('package_name'),
            Package.title.label('package_title'),
            Package.owner_org.label('owner_org'),
            Resource.id.label('resource_id'),
            Resource.name.label('resource_name'),
            Utilization.id.label('utilization_id'),
            literal('利活用申請').label('feedback_type'),
            literal(None).label('comment_id'),
            Utilization.title.label('content'),
            Utilization.created.label('created'),
            Utilization.approval.label('is_approved'),
        )
        .select_from(Package)
        .join(Group, Package.owner_org == Group.id)
        .join(Resource)
        .join(Utilization)
        .filter(
            Group.name.in_(org_names),
            Package.state == "active",
            Resource.state == "active",
        )
    )

    return query


def get_simple_utilizations_query(org_list):
    org_names = [org['name'] for org in org_list]

    query = (
        session.query(
            Group.name.label('group_name'),
            literal("利活用申請").label("feedback_type"),
            Utilization.approval.label('is_approved'),
        )
        .join(Package, Group.id == Package.owner_org)
        .join(Resource, Package.id == Resource.package_id)
        .join(Utilization, Resource.id == Utilization.resource_id)
        .filter(
            Group.name.in_(org_names),
            Package.state == "active",
            Resource.state == "active",
        )
    )

    return query


# Get utilizations using comment_id_list
def get_utilizations(comment_id_list):
    utilizations = (
        session.query(Utilization)
        .join(UtilizationComment)
        .filter(UtilizationComment.id.in_(comment_id_list))
    ).all()
    return utilizations


# Get the IDs of utilization where approval is False using utilization_id_list.
def get_utilization_ids(utilization_id_list):
    query = (
        session.query(Utilization.id)
        .filter(Utilization.id.in_(utilization_id_list))
        .filter(~Utilization.approval)
    )

    utilization_ids = [utilization.id for utilization in query.all()]

    return utilization_ids


def approve_utilization(utilization_id_list, approval_user_id):
    session.bulk_update_mappings(
        Utilization,
        [
            {
                'id': utilization_id,
                'approval': True,
                'approved': datetime.now(),
                'approval_user_id': approval_user_id,
            }
            for utilization_id in utilization_id_list
        ],
    )


def delete_utilization(utilization_id_list):
    (
        session.query(Utilization)
        .filter(Utilization.id.in_(utilization_id_list))
        .delete(synchronize_session='fetch')
    )
