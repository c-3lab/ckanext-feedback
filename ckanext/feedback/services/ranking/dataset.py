import calendar
import logging
from datetime import datetime

from ckan.model import Group, Package, Resource
from sqlalchemy import func

from ckanext.feedback.models.download import DownloadMonthly, DownloadSummary
from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


def get_download_ranking(
    top_ranked_limit,
    start_year_month,
    end_year_month,
    enable_org=None,
):
    download_count_by_period = get_download_count_by_period(
        start_year_month, end_year_month
    )
    total_download_count = get_total_download_count()

    query = (
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
        .filter(
            Package.state == 'active',
            Group.state == 'active',
        )
    )

    if enable_org and enable_org != [None]:
        query = query.filter(Group.name.in_(enable_org))

    query = (
        query.order_by(download_count_by_period.c.download_count.desc())
        .limit(top_ranked_limit)
        .all()
    )

    return query


def get_last_day_of_month(year, month):
    _, last_day = calendar.monthrange(year, month)
    return last_day


def get_download_count_by_period(start_year_month, end_year_month):
    start_date = datetime.strptime(start_year_month, '%Y-%m')
    end_date = datetime.strptime(end_year_month, '%Y-%m')
    end_year, end_month = end_date.year, end_date.month
    end_date = end_date.replace(day=get_last_day_of_month(end_year, end_month))
    end_date = end_date.replace(hour=23, minute=59, second=59)

    query = (
        session.query(
            Resource.package_id.label('package_id'),
            func.sum(DownloadMonthly.download_count).label('download_count'),
        )
        .join(DownloadMonthly, Resource.id == DownloadMonthly.resource_id, isouter=True)
        .filter(
            Resource.state == 'active',
            func.date(DownloadMonthly.created) >= start_date,
            func.date(DownloadMonthly.created) <= end_date,
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
        .filter(Resource.state == 'active')
        .group_by(Resource.package_id)
        .subquery()
    )
    return query
