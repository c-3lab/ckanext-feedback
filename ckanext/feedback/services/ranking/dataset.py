import calendar
import logging
from datetime import datetime

from ckan.model import Group, Package, Resource
from sqlalchemy import func

from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


def get_generic_ranking(
    top_ranked_limit,
    start_year_month,
    end_year_month,
    period_model,
    period_column,
    total_model,
    total_column,
    enable_org=None,
    organization_name=None,
):
    count_by_period = get_count_by_period(
        period_model, period_column, start_year_month, end_year_month
    )
    total_count = get_total_count(total_model, total_column)
    query = (
        session.query(
            Group.name,
            Group.title,
            Package.name,
            Package.title,
            Package.notes,
            count_by_period.c.count.label("count_by_period"),
            total_count.c.count.label("total_count"),
        )
        .join(count_by_period, Package.id == count_by_period.c.package_id)
        .join(total_count, Package.id == total_count.c.package_id)
        .join(Group, Package.owner_org == Group.id)
        .filter(
            Package.state == 'active',
            Group.state == 'active',
        )
    )
    if enable_org and enable_org != [None]:
        query = query.filter(Group.name.in_(enable_org))

    if organization_name:
        query = query.filter(Group.name == organization_name)

    query = query.order_by(count_by_period.c.count.desc()).limit(top_ranked_limit).all()
    return query


def get_last_day_of_month(year, month):
    _, last_day = calendar.monthrange(year, month)
    return last_day


def get_count_by_period(model, column, start_year_month, end_year_month):
    start_dt = datetime.strptime(start_year_month, '%Y-%m').replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    end_base = datetime.strptime(end_year_month, '%Y-%m').replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    # 次月1日（排他的上限）
    if end_base.month == 12:
        next_month_start = end_base.replace(year=end_base.year + 1, month=1)
    else:
        next_month_start = end_base.replace(month=end_base.month + 1)

    query = (
        session.query(
            Resource.package_id.label('package_id'),
            func.sum(getattr(model, column)).label('count'),
        )
        .join(model, Resource.id == model.resource_id, isouter=True)
        .filter(
            Resource.state == 'active',
            model.created >= start_dt,
            model.created < next_month_start,
        )
        .group_by(Resource.package_id)
        .subquery()
    )
    return query


def get_total_count(total_model, total_column):
    query = (
        session.query(
            Resource.package_id.label('package_id'),
            func.sum(getattr(total_model, total_column)).label('count'),
        )
        .join(total_model, Resource.id == total_model.resource_id)
        .filter(Resource.state == 'active')
        .group_by(Resource.package_id)
        .subquery()
    )
    return query
