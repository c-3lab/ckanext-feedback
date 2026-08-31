import calendar
from datetime import datetime

from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource

from ckanext.feedback.models.resource_comment import ResourceComment
from ckanext.feedback.models.session import session


def create_comment_query(
    organization_name,
    start_date=None,
    end_date=None,
):
    query = (
        session.query(
            Resource.id.label("resource_id"),
            Group.title.label("organization_title"),
            Package.title.label("package_title"),
            Resource.name.label("resource_name"),
            ResourceComment.content.label("comment_content"),
            ResourceComment.created.label("created"),
        )
        .select_from(ResourceComment)
        .join(
            Resource,
            ResourceComment.resource_id == Resource.id,
        )
        .join(
            Package,
            Resource.package_id == Package.id,
        )
        .join(
            Group,
            Package.owner_org == Group.id,
        )
        .filter(
            ResourceComment.approval.is_(True),
            Resource.state == "active",
            Package.state == "active",
            Group.state == "active",
        )
    )

    if organization_name:
        query = query.filter(Group.name == organization_name)

    if start_date and end_date:
        query = query.filter(
            ResourceComment.created.between(
                start_date,
                end_date,
            )
        )

    return query.order_by(ResourceComment.created.asc())


def get_monthly_comments(
    organization_name,
    select_month,
):
    year, month = map(int, select_month.split("-"))

    last_day = calendar.monthrange(year, month)[1]

    start_date = datetime(
        year,
        month,
        1,
        0,
        0,
        0,
    )

    end_date = datetime(
        year,
        month,
        last_day,
        23,
        59,
        59,
    )

    return create_comment_query(
        organization_name,
        start_date,
        end_date,
    )


def get_yearly_comments(
    organization_name,
    select_year,
):
    year = int(select_year)

    start_date = datetime(
        year,
        1,
        1,
        0,
        0,
        0,
    )

    end_date = datetime(
        year,
        12,
        31,
        23,
        59,
        59,
    )

    return create_comment_query(
        organization_name,
        start_date,
        end_date,
    )


def get_all_time_comments(
    organization_name,
):
    return create_comment_query(organization_name)
