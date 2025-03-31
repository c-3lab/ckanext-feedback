import calendar
import logging
from datetime import date

from ckan.common import _, config
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


def create_resource_report_query(
    download_subquery,
    resource_comment_subquery,
    utilization_subquery,
    utilization_comment_subquery,
    issue_resolution_subquery,
    like_subquery,
    rating_subquery,
):
    query = (
        session.query(
            Resource.id.label("resource_id"),
            func.coalesce(download_subquery.c.download_count, 0),
            func.coalesce(resource_comment_subquery.c.comment_count, 0),
            func.coalesce(utilization_subquery.c.utilization_count, 0),
            func.coalesce(utilization_comment_subquery.c.utilization_comment_count, 0),
            func.coalesce(issue_resolution_subquery.c.issue_resolution_count, 0),
            func.coalesce(like_subquery.c.like_count, 0),
            rating_subquery.c.average_rating,
        )
        .select_from(Group)
        .join(Package, Group.id == Package.owner_org)
        .join(Resource, Package.id == Resource.package_id)
        # TODO: フロントから送信された組織でフィルターを掛けられるようにする
        .filter(Group.name == 'organization-name-a')
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


def get_resource_statistics_with_details(query):
    results = []

    for row in query.all():
        group_title, package_title, resource_name, resource_link = get_resource_details(
            row.resource_id
        )

        results.append(
            {
                _("resource_id"): row.resource_id,
                _("group_title"): group_title,
                _("package_title"): package_title,
                _("resource_name"): resource_name,
                _("download_count"): row[1],
                _("comment_count"): row[2],
                _("utilization_count"): row[3],
                _("utilization_comment_count"): row[4],
                _("issue_resolution_count"): row[5],
                _("like_count"): row[6],
                _("average_rating"): (
                    float(row[7]) if row[7] is not None else _("Not rated")
                ),
                "url": resource_link,
            }
        )

    return results


def get_monthly_data(select_month):
    year, month = map(int, select_month.split('-'))
    last_day = calendar.monthrange(year, month)[1]

    download_subquery = (
        session.query(
            DownloadMonthly.resource_id,
            func.sum(DownloadMonthly.download_count).label('download_count'),
        )
        .filter(
            DownloadMonthly.created.between(
                date(year, month, 1), date(year, month, last_day)
            )
        )
        .group_by(DownloadMonthly.resource_id)
        .subquery()
    )

    resource_comment_subquery = (
        session.query(
            ResourceComment.resource_id,
            func.count(ResourceComment.id).label('comment_count'),
        )
        .filter(
            ResourceComment.approval.is_(True),
            ResourceComment.created.between(
                date(year, month, 1), date(year, month, last_day)
            ),
        )
        .group_by(ResourceComment.resource_id)
        .subquery()
    )

    utilization_subquery = (
        session.query(
            Utilization.resource_id,
            func.count(Utilization.id).label('utilization_count'),
        )
        .filter(
            Utilization.approval.is_(True),
            Utilization.created.between(
                date(year, month, 1), date(year, month, last_day)
            ),
        )
        .group_by(Utilization.resource_id)
        .subquery()
    )

    utilization_comment_subquery = (
        session.query(
            Utilization.resource_id,
            func.count(UtilizationComment.id).label('utilization_comment_count'),
        )
        .join(Utilization, UtilizationComment.utilization_id == Utilization.id)
        .filter(
            Utilization.approval.is_(True),
            UtilizationComment.created.between(
                date(year, month, 1), date(year, month, last_day)
            ),
        )
        .group_by(Utilization.resource_id)
        .subquery()
    )

    issue_resolution_subquery = (
        session.query(
            Utilization.resource_id,
            func.count(IssueResolution.id).label('issue_resolution_count'),
        )
        .join(Utilization, IssueResolution.utilization_id == Utilization.id)
        .filter(
            IssueResolution.created.between(
                date(year, month, 1), date(year, month, last_day)
            )
        )
        .group_by(Utilization.resource_id)
        .subquery()
    )

    like_subquery = (
        session.query(
            ResourceLikeMonthly.resource_id,
            func.sum(ResourceLikeMonthly.like_count).label('like_count'),
        )
        .filter(
            ResourceLikeMonthly.created.between(
                date(year, month, 1), date(year, month, last_day)
            )
        )
        .group_by(ResourceLikeMonthly.resource_id)
        .subquery()
    )

    rating_subquery = (
        session.query(
            ResourceComment.resource_id,
            func.avg(ResourceComment.rating.cast(Float)).label('average_rating'),
        )
        .filter(
            ResourceComment.approval.is_(True),
            ResourceComment.rating.isnot(None),
            ResourceComment.created.between(
                date(year, month, 1), date(year, month, last_day)
            ),
        )
        .group_by(
            ResourceComment.resource_id,
        )
        .subquery()
    )

    query = create_resource_report_query(
        download_subquery,
        resource_comment_subquery,
        utilization_subquery,
        utilization_comment_subquery,
        issue_resolution_subquery,
        like_subquery,
        rating_subquery,
    )

    return get_resource_statistics_with_details(query)


def get_yearly_data(select_year):
    year = int(select_year)

    download_subquery = (
        session.query(
            DownloadMonthly.resource_id,
            func.sum(DownloadMonthly.download_count).label('download_count'),
        )
        .filter(DownloadMonthly.created.between(date(year, 1, 1), date(year, 12, 31)))
        .group_by(DownloadMonthly.resource_id)
        .subquery()
    )

    resource_comment_subquery = (
        session.query(
            ResourceComment.resource_id,
            func.count(ResourceComment.id).label('comment_count'),
        )
        .filter(
            ResourceComment.approval.is_(True),
            ResourceComment.created.between(date(year, 1, 1), date(year, 12, 31)),
        )
        .group_by(ResourceComment.resource_id)
        .subquery()
    )

    utilization_subquery = (
        session.query(
            Utilization.resource_id,
            func.count(Utilization.id).label('utilization_count'),
        )
        .filter(
            Utilization.approval.is_(True),
            Utilization.created.between(date(year, 1, 1), date(year, 12, 31)),
        )
        .group_by(Utilization.resource_id)
        .subquery()
    )

    utilization_comment_subquery = (
        session.query(
            Utilization.resource_id,
            func.count(UtilizationComment.id).label('utilization_comment_count'),
        )
        .join(Utilization, UtilizationComment.utilization_id == Utilization.id)
        .filter(
            Utilization.approval.is_(True),
            UtilizationComment.created.between(date(year, 1, 1), date(year, 12, 31)),
        )
        .group_by(Utilization.resource_id)
        .subquery()
    )

    issue_resolution_subquery = (
        session.query(
            Utilization.resource_id,
            func.count(IssueResolution.id).label('issue_resolution_count'),
        )
        .join(Utilization, IssueResolution.utilization_id == Utilization.id)
        .filter(IssueResolution.created.between(date(year, 1, 1), date(year, 12, 31)))
        .group_by(Utilization.resource_id)
        .subquery()
    )

    like_subquery = (
        session.query(
            ResourceLikeMonthly.resource_id,
            func.sum(ResourceLikeMonthly.like_count).label('like_count'),
        )
        .filter(
            ResourceLikeMonthly.created.between(date(year, 1, 1), date(year, 12, 31))
        )
        .group_by(ResourceLikeMonthly.resource_id)
        .subquery()
    )

    rating_subquery = (
        session.query(
            ResourceComment.resource_id,
            func.avg(ResourceComment.rating.cast(Float)).label('average_rating'),
        )
        .filter(
            ResourceComment.approval.is_(True),
            ResourceComment.rating.isnot(None),
            ResourceComment.created.between(date(year, 1, 1), date(year, 12, 31)),
        )
        .group_by(
            ResourceComment.resource_id,
        )
        .subquery()
    )

    query = create_resource_report_query(
        download_subquery,
        resource_comment_subquery,
        utilization_subquery,
        utilization_comment_subquery,
        issue_resolution_subquery,
        like_subquery,
        rating_subquery,
    )

    return get_resource_statistics_with_details(query)


def get_all_time_data():
    download_subquery = (
        session.query(
            DownloadMonthly.resource_id,
            func.sum(DownloadMonthly.download_count).label('download_count'),
        )
        .group_by(DownloadMonthly.resource_id)
        .subquery()
    )

    resource_comment_subquery = (
        session.query(
            ResourceComment.resource_id,
            func.count(ResourceComment.id).label('comment_count'),
        )
        .filter(ResourceComment.approval.is_(True))
        .group_by(ResourceComment.resource_id)
        .subquery()
    )

    utilization_subquery = (
        session.query(
            Utilization.resource_id,
            func.count(Utilization.id).label('utilization_count'),
        )
        .filter(Utilization.approval.is_(True))
        .group_by(Utilization.resource_id)
        .subquery()
    )

    utilization_comment_subquery = (
        session.query(
            Utilization.resource_id,
            func.count(UtilizationComment.id).label('utilization_comment_count'),
        )
        .join(Utilization, UtilizationComment.utilization_id == Utilization.id)
        .filter(Utilization.approval.is_(True))
        .group_by(Utilization.resource_id)
        .subquery()
    )

    issue_resolution_subquery = (
        session.query(
            Utilization.resource_id,
            func.count(IssueResolution.id).label('issue_resolution_count'),
        )
        .join(Utilization, IssueResolution.utilization_id == Utilization.id)
        .group_by(Utilization.resource_id)
        .subquery()
    )

    like_subquery = (
        session.query(
            ResourceLikeMonthly.resource_id,
            func.sum(ResourceLikeMonthly.like_count).label('like_count'),
        )
        .group_by(ResourceLikeMonthly.resource_id)
        .subquery()
    )

    rating_subquery = (
        session.query(
            ResourceComment.resource_id,
            func.avg(ResourceComment.rating.cast(Float)).label('average_rating'),
        )
        .filter(ResourceComment.approval.is_(True), ResourceComment.rating.isnot(None))
        .group_by(
            ResourceComment.resource_id,
        )
        .subquery()
    )

    query = create_resource_report_query(
        download_subquery,
        resource_comment_subquery,
        utilization_subquery,
        utilization_comment_subquery,
        issue_resolution_subquery,
        like_subquery,
        rating_subquery,
    )

    return get_resource_statistics_with_details(query)
