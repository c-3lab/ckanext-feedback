import calendar
import logging
from datetime import datetime, timedelta

from ckan.common import _, config
from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from ckan.plugins import toolkit
from sqlalchemy import Date, Float, func

from ckanext.feedback.models.download import DownloadMonthly
from ckanext.feedback.models.issue import IssueResolution
from ckanext.feedback.models.likes import ResourceLikeMonthly
from ckanext.feedback.models.resource_comment import ResourceComment
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization, UtilizationComment

log = logging.getLogger(__name__)


def generate_months(start, end):
    months = []
    current = start
    while current <= end:
        months.append(current)
        current = (current.replace(day=1) + timedelta(days=32)).replace(day=1)
    return months


def get_monthly_data(start_month_str, end_month_str):
    start_date = datetime.strptime(start_month_str, '%Y-%m')

    end_year, end_month = map(int, end_month_str.split('-'))
    last_day = calendar.monthrange(end_year, end_month)[1]
    end_date = datetime(end_year, end_month, last_day, 23, 59, 59)

    months = generate_months(start_date, end_date)

    download_subquery = (
        session.query(
            DownloadMonthly.resource_id,
            func.date_trunc('month', DownloadMonthly.created).cast(Date).label('month'),
            func.sum(DownloadMonthly.download_count).label('download_count'),
        )
        .group_by(
            DownloadMonthly.resource_id,
            func.date_trunc('month', DownloadMonthly.created),
        )
        .subquery()
    )

    resource_comment_subquery = (
        session.query(
            ResourceComment.resource_id,
            func.date_trunc('month', ResourceComment.created).cast(Date).label('month'),
            func.count(ResourceComment.id).label('comment_count'),
        )
        .filter(ResourceComment.approval.is_(True))
        .group_by(
            ResourceComment.resource_id,
            func.date_trunc('month', ResourceComment.created),
        )
        .subquery()
    )

    utilization_subquery = (
        session.query(
            Utilization.resource_id,
            func.date_trunc('month', Utilization.created).cast(Date).label('month'),
            func.count(Utilization.id).label('utilization_count'),
        )
        .filter(Utilization.approval.is_(True))
        .group_by(
            Utilization.resource_id, func.date_trunc('month', Utilization.created)
        )
        .subquery()
    )

    utilization_comment_subquery = (
        session.query(
            Utilization.resource_id,
            func.date_trunc('month', UtilizationComment.created)
            .cast(Date)
            .label('month'),
            func.count(UtilizationComment.id).label('utilization_comment_count'),
        )
        .join(Utilization, UtilizationComment.utilization_id == Utilization.id)
        .filter(Utilization.approval.is_(True))
        .group_by(
            Utilization.resource_id,
            func.date_trunc('month', UtilizationComment.created),
        )
        .subquery()
    )

    issue_resolution_subquery = (
        session.query(
            Utilization.resource_id,
            func.date_trunc('month', IssueResolution.created).cast(Date).label('month'),
            func.count(IssueResolution.id).label('issue_resolution_count'),
        )
        .join(Utilization, IssueResolution.utilization_id == Utilization.id)
        .group_by(
            Utilization.resource_id, func.date_trunc('month', IssueResolution.created)
        )
        .subquery()
    )

    like_subquery = (
        session.query(
            ResourceLikeMonthly.resource_id,
            func.date_trunc('month', ResourceLikeMonthly.created)
            .cast(Date)
            .label('month'),
            func.sum(ResourceLikeMonthly.like_count).label('like_count'),
        )
        .group_by(
            ResourceLikeMonthly.resource_id,
            func.date_trunc('month', ResourceLikeMonthly.created),
        )
        .subquery()
    )

    rating_subquery = (
        session.query(
            ResourceComment.resource_id,
            func.date_trunc('month', ResourceComment.created).cast(Date).label('month'),
            func.avg(ResourceComment.rating.cast(Float)).label('average_rating'),
        )
        .filter(ResourceComment.approval.is_(True), ResourceComment.rating.isnot(None))
        .group_by(
            ResourceComment.resource_id,
            func.date_trunc('month', ResourceComment.created),
        )
        .subquery()
    )

    resource_ids = session.query(Resource.id).all()

    results = []
    for (resource_id,) in resource_ids:
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

        for month in months:
            download_row = (
                session.query(
                    func.coalesce(download_subquery.c.download_count, 0),
                )
                .filter(
                    download_subquery.c.resource_id == resource_id,
                    download_subquery.c.month == month,
                )
                .first()
            )

            resource_comment_row = (
                session.query(
                    func.coalesce(resource_comment_subquery.c.comment_count, 0),
                )
                .filter(
                    resource_comment_subquery.c.resource_id == resource_id,
                    resource_comment_subquery.c.month == month,
                )
                .first()
            )

            utilization_row = (
                session.query(
                    func.coalesce(utilization_subquery.c.utilization_count, 0),
                )
                .filter(
                    utilization_subquery.c.resource_id == resource_id,
                    utilization_subquery.c.month == month,
                )
                .first()
            )

            utilization_comment_row = (
                session.query(
                    func.coalesce(
                        utilization_comment_subquery.c.utilization_comment_count, 0
                    ),
                )
                .filter(
                    utilization_comment_subquery.c.resource_id == resource_id,
                    utilization_comment_subquery.c.month == month,
                )
                .first()
            )

            issue_resolution_row = (
                session.query(
                    func.coalesce(
                        issue_resolution_subquery.c.issue_resolution_count, 0
                    ),
                )
                .filter(
                    issue_resolution_subquery.c.resource_id == resource_id,
                    issue_resolution_subquery.c.month == month,
                )
                .first()
            )

            like_row = (
                session.query(
                    func.coalesce(like_subquery.c.like_count, 0),
                )
                .filter(
                    like_subquery.c.resource_id == resource_id,
                    like_subquery.c.month == month,
                )
                .first()
            )

            rating_row = (
                session.query(rating_subquery.c.average_rating)
                .filter(
                    rating_subquery.c.resource_id == resource_id,
                    rating_subquery.c.month == month,
                )
                .first()
            )

            results.append(
                {
                    _("date"): month,
                    _("resource_id"): resource_id,
                    _("group_title"): group_title,
                    _("package_title"): package_title,
                    _("resource_name"): resource_name,
                    _("download_count"): download_row[0] if download_row else 0,
                    _("comment_count"): (
                        resource_comment_row[0] if resource_comment_row else 0
                    ),
                    _("utilization_count"): (
                        utilization_row[0] if utilization_row else 0
                    ),
                    _("utilization_comment_count"): (
                        utilization_comment_row[0] if utilization_comment_row else 0
                    ),
                    _("issue_resolution_count"): (
                        issue_resolution_row[0] if issue_resolution_row else 0
                    ),
                    _("like_count"): like_row[0] if like_row else 0,
                    _("average_rating"): (
                        float(rating_row[0])
                        if rating_row and rating_row[0] is not None
                        else _("Not rated")
                    ),
                    _("url"): resource_link,
                }
            )

    return results
