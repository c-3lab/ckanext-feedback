import calendar
import logging
from datetime import date

from ckan.common import config
from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from ckan.plugins import toolkit
from sqlalchemy import Float, func

from ckanext.feedback.models.download import DownloadMonthly
from ckanext.feedback.models.issue import IssueResolution
from ckanext.feedback.models.likes import ResourceLikeMonthly
from ckanext.feedback.models.resource_comment import ResourceComment
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization, UtilizationComment

log = logging.getLogger(__name__)


def get_resource_details(resource_id):
    resources = (
        session.query(Group.title, Package.name, Package.title, Resource.name)
        .join(Package, Resource.package_id == Package.id)
        .join(Group, Package.owner_org == Group.id)
        .filter(Resource.id == resource_id)
        .first()
    )

    group_title, package_name, package_title, resource_name = resources

    site_url = config.get('ckan.site_url', '')
    resource_path = toolkit.url_for(
        'resource.read', id=package_name, resource_id=resource_id
    )
    resource_link = f"{site_url}{resource_path}"

    return group_title, package_title, resource_name, resource_link


def get_download_subquery(start_date=None, end_date=None):
    query = session.query(
        DownloadMonthly.resource_id,
        func.sum(DownloadMonthly.download_count).label('download_count'),
    )

    if start_date and end_date:
        query = query.filter(DownloadMonthly.created.between(start_date, end_date))

    query = query.group_by(DownloadMonthly.resource_id)

    return query.subquery()


def get_resource_comment_subquery(start_date=None, end_date=None):
    query = session.query(
        ResourceComment.resource_id,
        func.count(ResourceComment.id).label('comment_count'),
    ).filter(ResourceComment.approval.is_(True))

    if start_date and end_date:
        query = query.filter(ResourceComment.created.between(start_date, end_date))

    query = query.group_by(ResourceComment.resource_id)

    return query.subquery()


def get_utilization_subquery(start_date=None, end_date=None):
    query = session.query(
        Utilization.resource_id,
        func.count(Utilization.id).label('utilization_count'),
    ).filter(Utilization.approval.is_(True))

    if start_date and end_date:
        query = query.filter(Utilization.created.between(start_date, end_date))

    query = query.group_by(Utilization.resource_id)

    return query.subquery()


def get_utilization_comment_subquery(start_date=None, end_date=None):
    query = (
        session.query(
            Utilization.resource_id,
            func.count(UtilizationComment.id).label('utilization_comment_count'),
        )
        .join(Utilization, UtilizationComment.utilization_id == Utilization.id)
        .filter(Utilization.approval.is_(True))
    )

    if start_date and end_date:
        query = query.filter(UtilizationComment.created.between(start_date, end_date))

    query = query.group_by(Utilization.resource_id)

    return query.subquery()


def get_issue_resolution_subquery(start_date=None, end_date=None):
    query = session.query(
        Utilization.resource_id,
        func.count(IssueResolution.id).label('issue_resolution_count'),
    ).join(Utilization, IssueResolution.utilization_id == Utilization.id)

    if start_date and end_date:
        query = query.filter(IssueResolution.created.between(start_date, end_date))

    query = query.group_by(Utilization.resource_id)

    return query.subquery()


def get_like_subquery(start_date=None, end_date=None):
    query = session.query(
        ResourceLikeMonthly.resource_id,
        func.sum(ResourceLikeMonthly.like_count).label('like_count'),
    )

    if start_date and end_date:
        query = query.filter(ResourceLikeMonthly.created.between(start_date, end_date))

    query = query.group_by(ResourceLikeMonthly.resource_id)

    return query.subquery()


def get_rating_subquery(start_date=None, end_date=None):
    query = session.query(
        ResourceComment.resource_id,
        func.avg(ResourceComment.rating.cast(Float)).label('average_rating'),
    ).filter(
        ResourceComment.approval.is_(True),
        ResourceComment.rating.isnot(None),
    )

    if start_date and end_date:
        query = query.filter(ResourceComment.created.between(start_date, end_date))

    query = query.group_by(ResourceComment.resource_id)

    return query.subquery()


def create_resource_report_query(
    download_subquery,
    resource_comment_subquery,
    utilization_subquery,
    utilization_comment_subquery,
    issue_resolution_subquery,
    like_subquery,
    rating_subquery,
    organization_name,
):
    query = (
        session.query(
            Resource.id.label("resource_id"),
            func.coalesce(download_subquery.c.download_count, 0).label("download"),
            func.coalesce(resource_comment_subquery.c.comment_count, 0).label(
                "resource_comment"
            ),
            func.coalesce(utilization_subquery.c.utilization_count, 0).label(
                "utilization"
            ),
            func.coalesce(
                utilization_comment_subquery.c.utilization_comment_count, 0
            ).label("utilization_comment"),
            func.coalesce(issue_resolution_subquery.c.issue_resolution_count, 0).label(
                "issue_resolution"
            ),
            func.coalesce(like_subquery.c.like_count, 0).label("like"),
            rating_subquery.c.average_rating.label("rating"),
        )
        .select_from(Group)
        .join(Package, Group.id == Package.owner_org)
        .join(Resource, Package.id == Resource.package_id)
        .filter(Group.name == organization_name)
        .outerjoin(download_subquery, Resource.id == download_subquery.c.resource_id)
        .outerjoin(
            resource_comment_subquery,
            Resource.id == resource_comment_subquery.c.resource_id,
        )
        .outerjoin(
            utilization_subquery, Resource.id == utilization_subquery.c.resource_id
        )
        .outerjoin(
            utilization_comment_subquery,
            Resource.id == utilization_comment_subquery.c.resource_id,
        )
        .outerjoin(
            issue_resolution_subquery,
            Resource.id == issue_resolution_subquery.c.resource_id,
        )
        .outerjoin(like_subquery, Resource.id == like_subquery.c.resource_id)
        .outerjoin(rating_subquery, Resource.id == rating_subquery.c.resource_id)
    )

    return query


def get_monthly_data(organization_name, select_month):
    year, month = map(int, select_month.split('-'))
    last_day = calendar.monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    download_subquery = get_download_subquery(start_date, end_date)
    resource_comment_subquery = get_resource_comment_subquery(start_date, end_date)
    utilization_subquery = get_utilization_subquery(start_date, end_date)
    utilization_comment_subquery = get_utilization_comment_subquery(
        start_date, end_date
    )
    issue_resolution_subquery = get_issue_resolution_subquery(start_date, end_date)
    like_subquery = get_like_subquery(start_date, end_date)
    rating_subquery = get_rating_subquery(start_date, end_date)

    query = create_resource_report_query(
        download_subquery,
        resource_comment_subquery,
        utilization_subquery,
        utilization_comment_subquery,
        issue_resolution_subquery,
        like_subquery,
        rating_subquery,
        organization_name,
    )

    return query


def get_yearly_data(organization_name, select_year):
    year = int(select_year)
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    download_subquery = get_download_subquery(start_date, end_date)
    resource_comment_subquery = get_resource_comment_subquery(start_date, end_date)
    utilization_subquery = get_utilization_subquery(start_date, end_date)
    utilization_comment_subquery = get_utilization_comment_subquery(
        start_date, end_date
    )
    issue_resolution_subquery = get_issue_resolution_subquery(start_date, end_date)
    like_subquery = get_like_subquery(start_date, end_date)
    rating_subquery = get_rating_subquery(start_date, end_date)

    query = create_resource_report_query(
        download_subquery,
        resource_comment_subquery,
        utilization_subquery,
        utilization_comment_subquery,
        issue_resolution_subquery,
        like_subquery,
        rating_subquery,
        organization_name,
    )

    return query


def get_all_time_data(organization_name):
    download_subquery = get_download_subquery()
    resource_comment_subquery = get_resource_comment_subquery()
    utilization_subquery = get_utilization_subquery()
    utilization_comment_subquery = get_utilization_comment_subquery()
    issue_resolution_subquery = get_issue_resolution_subquery()
    like_subquery = get_like_subquery()
    rating_subquery = get_rating_subquery()

    query = create_resource_report_query(
        download_subquery,
        resource_comment_subquery,
        utilization_subquery,
        utilization_comment_subquery,
        issue_resolution_subquery,
        like_subquery,
        rating_subquery,
        organization_name,
    )

    return query
