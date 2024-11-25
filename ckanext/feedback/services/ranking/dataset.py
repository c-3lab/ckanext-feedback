import logging

from ckan.model import Group, Package, Resource
from sqlalchemy import extract, func

from ckanext.feedback.models.download import DownloadMonthly, DownloadSummary
from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


def get_download_ranking(
    enable_org,
    top_ranked_limit,
    period_months_ago,
    start_year_month=None,
    end_year_month=None,
):
    download_count_by_period = get_download_count_by_period(
        start_year_month, end_year_month
    )
    total_download_count = get_total_download_count()

    query = (
        (
            session.query(
                Group.name,
                Group.title,
                Package.name,
                Package.title,
                Package.notes,
                download_count_by_period.c.download_count,
                total_download_count.c.download_count,
            )
            .join(
                download_count_by_period,
                Package.id == download_count_by_period.c.package_id,
            )
            .join(total_download_count, Package.id == total_download_count.c.package_id)
            .join(Group, Package.owner_org == Group.id)
            .filter(Group.name.in_(enable_org))
            .order_by(download_count_by_period.c.download_count.desc())
        )
        .limit(top_ranked_limit)
        .all()
    )

    return query


def get_download_count_by_period(start_year_month, end_year_month):
    start_year, start_month = map(int, start_year_month.split('-'))
    end_year, end_month = map(int, end_year_month.split('-'))

    query = (
        session.query(
            Resource.package_id.label('package_id'),
            func.sum(DownloadMonthly.download_count).label('download_count'),
        )
        .join(DownloadMonthly, Resource.id == DownloadMonthly.resource_id, isouter=True)
        .filter(
            extract('year', DownloadMonthly.created) >= start_year,
            extract('month', DownloadMonthly.created) >= start_month,
            extract('year', DownloadMonthly.created) <= end_year,
            extract('month', DownloadMonthly.created) <= end_month,
        )
        .group_by(Resource.package_id)
        .subquery()
    )
    return query


def get_total_download_count():
    query = (
        session.query(
            Resource.package_id.label('package_id'),
            func.sum(DownloadSummary.download).label('download_count'),
        )
        .join(DownloadSummary, Resource.id == DownloadSummary.resource_id)
        .group_by(Resource.package_id)
        .subquery()
    )
    return query
