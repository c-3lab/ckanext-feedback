import calendar
from collections import namedtuple
from datetime import datetime

from ckan.model.group import Group
from ckan.model.package import Package
from ckan.model.resource import Resource
from sqlalchemy import or_

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentReply,
)
from ckanext.feedback.models.session import session

CommentCsvRow = namedtuple(
    'CommentCsvRow',
    [
        'resource_id',
        'organization_title',
        'package_title',
        'resource_name',
        'comment_content',
        'comment_reply',
        'created',
        'rating',
        'category',
    ],
)


def _apply_common_filters(query, organization_name):
    if organization_name:
        query = query.filter(Group.name == organization_name)
    return query


def _reply_comment_ids_in_period(organization_name, start_date, end_date):
    query = (
        session.query(ResourceCommentReply.resource_comment_id)
        .join(
            ResourceComment,
            ResourceCommentReply.resource_comment_id == ResourceComment.id,
        )
        .join(Resource, ResourceComment.resource_id == Resource.id)
        .join(Package, Resource.package_id == Package.id)
        .join(Group, Package.owner_org == Group.id)
        .filter(
            ResourceCommentReply.approval.is_(True),
            ResourceComment.approval.is_(True),
            Resource.state == "active",
            Package.state == "active",
            Group.state == "active",
            ResourceCommentReply.created.between(start_date, end_date),
        )
    )
    return _apply_common_filters(query, organization_name)


def _get_comments(organization_name, start_date=None, end_date=None):
    query = (
        session.query(
            ResourceComment.id.label("comment_id"),
            Resource.id.label("resource_id"),
            Group.title.label("organization_title"),
            Package.title.label("package_title"),
            Resource.name.label("resource_name"),
            ResourceComment.content.label("comment_content"),
            ResourceComment.created.label("created"),
            ResourceComment.rating.label("rating"),
            ResourceComment.category.label("category"),
        )
        .select_from(ResourceComment)
        .join(Resource, ResourceComment.resource_id == Resource.id)
        .join(Package, Resource.package_id == Package.id)
        .join(Group, Package.owner_org == Group.id)
        .filter(
            ResourceComment.approval.is_(True),
            Resource.state == "active",
            Package.state == "active",
            Group.state == "active",
        )
    )
    query = _apply_common_filters(query, organization_name)

    if start_date and end_date:
        query = query.filter(
            or_(
                ResourceComment.created.between(start_date, end_date),
                ResourceComment.id.in_(
                    _reply_comment_ids_in_period(
                        organization_name,
                        start_date,
                        end_date,
                    )
                ),
            )
        )

    return query.order_by(Resource.id, ResourceComment.created)


def _get_replies_by_comment_id(comment_ids):
    if not comment_ids:
        return {}

    replies = (
        session.query(
            ResourceCommentReply.resource_comment_id,
            ResourceCommentReply.content,
        )
        .filter(
            ResourceCommentReply.resource_comment_id.in_(comment_ids),
            ResourceCommentReply.approval.is_(True),
        )
        .order_by(
            ResourceCommentReply.resource_comment_id,
            ResourceCommentReply.created,
        )
        .all()
    )

    replies_by_comment_id = {}
    for comment_id, content in replies:
        replies_by_comment_id.setdefault(comment_id, []).append(content)
    return replies_by_comment_id


def _expand_comment_rows(comments, replies_by_comment_id):
    rows = []

    for comment in comments:
        replies = replies_by_comment_id.get(comment.comment_id, [])
        base_fields = {
            'resource_id': comment.resource_id,
            'organization_title': comment.organization_title,
            'package_title': comment.package_title,
            'resource_name': comment.resource_name,
        }

        if not replies:
            rows.append(
                CommentCsvRow(
                    **base_fields,
                    comment_content=comment.comment_content,
                    comment_reply='',
                    created=comment.created,
                    rating=comment.rating,
                    category=comment.category,
                )
            )
            continue

        for index, reply_content in enumerate(replies):
            rows.append(
                CommentCsvRow(
                    **base_fields,
                    comment_content=comment.comment_content if index == 0 else '',
                    comment_reply=reply_content,
                    created=comment.created if index == 0 else None,
                    rating=comment.rating if index == 0 else None,
                    category=comment.category if index == 0 else None,
                )
            )

    return rows


def get_comments(organization_name, start_date=None, end_date=None):
    comments = _get_comments(organization_name, start_date, end_date).all()
    comment_ids = [comment.comment_id for comment in comments]
    replies_by_comment_id = _get_replies_by_comment_id(comment_ids)
    return _expand_comment_rows(comments, replies_by_comment_id)


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

    return get_comments(
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

    return get_comments(
        organization_name,
        start_date,
        end_date,
    )


def get_all_time_comments(
    organization_name,
):
    return get_comments(organization_name)
