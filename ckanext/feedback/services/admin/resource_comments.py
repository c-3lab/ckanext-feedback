from datetime import datetime

from ckan.common import config
from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
<<<<<<< HEAD:ckanext/feedback/services/admin/resource_comments.py
from sqlalchemy import func, literal
=======
from sqlalchemy import desc, func
>>>>>>> 30b8a75 (Implement basic features for the admin panel):ckanext/feedback/services/management/comments.py

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentSummary,
)
from ckanext.feedback.models.session import session


def get_resource_comments_query(org_list):
    org_names = [org['name'] for org in org_list]

    query = (
        session.query(
            Group.name.label('group_name'),
            Package.name.label('package_name'),
            Package.title.label('package_title'),
            Package.owner_org.label('owner_org'),
            Resource.id.label('resource_id'),
            Resource.name.label('resource_name'),
            literal(None).label('utilization_id'),
            literal('リソースコメント').label('feedback_type'),
            ResourceComment.id.label('comment_id'),
            ResourceComment.content.label('content'),
            ResourceComment.created.label('created'),
            ResourceComment.approval.label('is_approved'),
        )
        .select_from(Package)
        .join(Group, Package.owner_org == Group.id)
        .join(Resource)
        .join(ResourceComment)
        .filter(Group.name.in_(org_names))
    )

    return query


def get_simple_resource_comments_query(org_list):
    org_names = [org['name'] for org in org_list]

<<<<<<< HEAD:ckanext/feedback/services/admin/resource_comments.py
    query = (
        session.query(
            Group.name.label('group_name'),
            literal("リソースコメント").label("feedback_type"),
            ResourceComment.approval.label('is_approved'),
        )
        .join(Package, Group.id == Package.owner_org)
        .join(Resource, Package.id == Resource.package_id)
        .join(ResourceComment, Resource.id == ResourceComment.resource_id)
        .filter(Group.name.in_(org_names))
=======

# Get the IDs of utilization where approval is False using utilization_id_list.
def get_utilization_ids(utilization_id_list):
    query = (
        session.query(Utilization.id)
        .filter(Utilization.id.in_(utilization_id_list))
        .filter(~Utilization.approval)
    )

    utilization_ids = [utilization.id for utilization in query.all()]

    return utilization_ids


# Get the IDs of utilization_comments where approval is False using comment_id_list.
def get_utilization_comment_ids(comment_id_list):
    query = (
        session.query(UtilizationComment.id)
        .filter(UtilizationComment.id.in_(comment_id_list))
        .filter(~UtilizationComment.approval)
    )

    comment_ids = [comment.id for comment in query.all()]

    return comment_ids


# Get organization using owner_org
def get_organization(owner_org):
    organization = session.query(Group).filter(Group.id == owner_org).first()
    return organization


# Recalculate total approved bulk utilizations comments
def refresh_utilizations_comments(utilizations):
    session.bulk_update_mappings(
        Utilization,
        [
            {
                'id': utilization.id,
                'comment': get_utilization_comments(utilization.id),
                'updated': datetime.now(),
            }
            for utilization in utilizations
        ],
>>>>>>> dac8944 (Add logic to skip re-approval for already approved items):ckanext/feedback/services/management/comments.py
    )

    return query


# Get the IDs of resource_comments where approval is False using comment_id_list.
def get_resource_comment_ids(comment_id_list):
    query = (
        session.query(ResourceComment.id)
        .filter(ResourceComment.id.in_(comment_id_list))
        .filter(~ResourceComment.approval)
    )

    comment_ids = [comment.id for comment in query.all()]

    return comment_ids


# Get the IDs of resource_comments where approval is False using comment_id_list.
def get_resource_comment_ids(comment_id_list):
    query = (
        session.query(ResourceComment.id)
        .filter(ResourceComment.id.in_(comment_id_list))
        .filter(~ResourceComment.approval)
    )

    comment_ids = [comment.id for comment in query.all()]

    return comment_ids


# Get resource comment summaries using comment_id_list
def get_resource_comment_summaries(comment_id_list):
    resource_comment_summaries = (
        session.query(ResourceCommentSummary)
        .join(Resource)
        .join(ResourceComment)
        .filter(ResourceComment.id.in_(comment_id_list))
    ).all()
    return resource_comment_summaries


<<<<<<< HEAD:ckanext/feedback/services/admin/resource_comments.py
# Approve selected resource comments
def approve_resource_comments(comment_id_list, approval_user_id):
    session.bulk_update_mappings(
        ResourceComment,
        [
            {
                'id': comment_id,
                'approval': True,
                'approved': datetime.now(),
                'approval_user_id': approval_user_id,
            }
            for comment_id in comment_id_list
        ],
    )


# Delete selected resource comments
def delete_resource_comments(comment_id_list):
    (
        session.query(ResourceComment)
        .filter(ResourceComment.id.in_(comment_id_list))
        .delete(synchronize_session='fetch')
    )
=======
def get_non_approve_contests(owner_orgs=None, limit=None, offset=None):
    resource_comments = session.query(
        ResourceComment.id,
        ResourceComment.resource.package.name.label('dataset_title'),
        ResourceComment.resource.name.label('resource_title'),
        ResourceComment.content.label('content'),
        ResourceComment.approval,
    ).filter(ResourceComment.approval is False)
    if owner_orgs is not None:
        resource_comments = (
            resource_comments.join(Resource)
            .join(Package)
            .filter(Package.owner_org.in_(owner_orgs))
        )

    utilizations = session.query(
        Utilization.id,
        Utilization.resource.package.name.label('dataset_title'),
        Utilization.resource.resource.name.label('resource_title'),
        Utilization.title.label('content'),
        Utilization.approval,
    ).filter(Utilization.approval is False)
    if owner_orgs is not None:
        utilizations = utilizations.join(Package).filter(
            Package.owner_org.in_(owner_orgs)
        )

    utilization_comments = session.query(
        UtilizationComment.id,
        UtilizationComment.utilization.resource.package.name.label('dataset_title'),
        UtilizationComment.utilization.resource.resource.name.label('resource_title'),
        UtilizationComment.utilization.title.label('content'),
        UtilizationComment.approval,
    ).filter(UtilizationComment.approval is False)
    if owner_orgs is not None:
        utilization_comments = (
            utilization_comments.join(Utilization)
            .join(Resource)
            .join(Package)
            .filter(Package.owner_org.in_(owner_orgs))
        )

    union_query = resource_comments.union_all(utilizations)
    union_query = union_query.union_all(utilization_comments)
    results = union_query.limit(limit).offset(offset).all()
    if limit is not None or offset is not None:
        total_count = union_query.count()
        return results, total_count
    return results
>>>>>>> 61f0718 (ページネーションバックエンド（検討・実装中）):ckanext/feedback/services/management/comments.py


# Recalculate total approved bulk resources comments
def refresh_resources_comments(resource_comment_summaries):
    mappings = []
    for resource_comment_summary in resource_comment_summaries:
        row = (
            session.query(
                func.sum(ResourceComment.rating).label('total_rating'),
                func.count().label('total_comment'),
                func.count(ResourceComment.rating).label('total_rating_comment'),
            )
            .filter(
                ResourceComment.resource_id == resource_comment_summary.resource.id,
                ResourceComment.approval,
            )
            .first()
        )
        if row.total_rating is None:
            rating = 0
        else:
            rating = row.total_rating / row.total_rating_comment
        mappings.append(
            {
                'id': resource_comment_summary.id,
                'comment': row.total_comment,
                'rating_comment': row.total_rating_comment,
                'rating': rating,
                'updated': datetime.now(),
            }
        )
    session.bulk_update_mappings(ResourceCommentSummary, mappings)
<<<<<<< HEAD:ckanext/feedback/services/admin/resource_comments.py
=======


# Approve selected utilization comments
def approve_utilization_comments(comment_id_list, approval_user_id):
    session.bulk_update_mappings(
        UtilizationComment,
        [
            {
                'id': comment_id,
                'approval': True,
                'approved': datetime.now(),
                'approval_user_id': approval_user_id,
            }
            for comment_id in comment_id_list
        ],
    )


# Delete selected utilization comments
def delete_utilization_comments(comment_id_list):
    (
        session.query(UtilizationComment)
        .filter(UtilizationComment.id.in_(comment_id_list))
        .delete(synchronize_session='fetch')
    )


# Approve selected resource comments
def approve_resource_comments(comment_id_list, approval_user_id):
    session.bulk_update_mappings(
        ResourceComment,
        [
            {
                'id': comment_id,
                'approval': True,
                'approved': datetime.now(),
                'approval_user_id': approval_user_id,
            }
            for comment_id in comment_id_list
        ],
    )


# Delete selected resource comments
def delete_resource_comments(comment_id_list):
    (
        session.query(ResourceComment)
        .filter(ResourceComment.id.in_(comment_id_list))
        .delete(synchronize_session='fetch')
    )


# Get the number of pages of selected resource comments
def get_page_for_resource_comment(resource_id, resource_comment_id):
    comments_per_page = config.get('ckan.datasets_per_page')

    #
    # Note: Ensure that the `order_by` used in this query is consistent
    # with the `order_by` in the get_resource_comments function.
    # The ordering must be the same for both functions.
    #
    query = (
        session.query(
            ResourceComment.id,
            func.row_number()
            .over(order_by=desc(ResourceComment.created))
            .label('row_num'),
        )
        .filter(ResourceComment.resource_id == resource_id)
        .subquery()
    )

    row_number = (
        session.query(query.c.row_num)
        .filter(query.c.id == resource_comment_id)
        .scalar()
    )

    page_number = (row_number - 1) // comments_per_page + 1

    return page_number


# Get the number of pages of selected utilization comments
def get_page_for_utilization_comment(utilization_id, utilization_comment_id):
    comments_per_page = config.get('ckan.datasets_per_page')

    query = (
        session.query(
            UtilizationComment.id,
            func.row_number()
            .over(order_by=desc(UtilizationComment.created))
            .label('row_num'),
        )
        .filter(UtilizationComment.utilization_id == utilization_id)
        .subquery()
    )

    row_number = (
        session.query(query.c.row_num)
        .filter(query.c.id == utilization_comment_id)
        .scalar()
    )

    page_number = (row_number - 1) // comments_per_page + 1

    return page_number
>>>>>>> 30b8a75 (Implement basic features for the admin panel):ckanext/feedback/services/management/comments.py
