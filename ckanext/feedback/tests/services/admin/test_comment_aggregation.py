import uuid
from datetime import datetime

import pytest
from ckan import model
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_resource_tables,
    drop_resource_tables,
)
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentCategory,
    ResourceCommentReply,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.services.admin import comment_aggregation

engine = model.repo.session.get_bind()


def _register_resource_comment(
    resource_id,
    content='parent comment',
    created=None,
    approval=True,
    rating=4,
):
    rc = ResourceComment(
        id=str(uuid.uuid4()),
        resource_id=resource_id,
        category=ResourceCommentCategory.QUESTION,
        content=content,
        rating=rating,
        created=created or datetime(2024, 3, 10, 10, 0, 0),
        approval=approval,
        approved=None,
        approval_user_id=None,
    )
    session.add(rc)
    return rc


def _register_reply(
    resource_comment_id,
    content='reply content',
    created=None,
    approval=True,
):
    rr = ResourceCommentReply(
        id=str(uuid.uuid4()),
        resource_comment_id=resource_comment_id,
        content=content,
        created=created or datetime(2024, 3, 10, 11, 0, 0),
        approval=approval,
        approved=None,
        approval_user_id=None,
    )
    session.add(rr)
    return rr


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestCommentAggregation:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        drop_resource_tables(engine)
        create_resource_tables(engine)

    def test_get_comments_outputs_comment_and_reply_on_separate_rows(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        parent = _register_resource_comment(
            res['id'],
            content='approved comment',
            created=datetime(2024, 3, 10, 10, 0, 0),
            approval=True,
        )
        _register_reply(
            parent.id,
            content='approved reply',
            created=datetime(2024, 3, 10, 11, 0, 0),
            approval=True,
        )
        _register_reply(
            parent.id,
            content='unapproved reply',
            created=datetime(2024, 3, 10, 12, 0, 0),
            approval=False,
        )

        session.commit()

        rows = comment_aggregation.get_comments(org['name'])

        assert len(rows) == 2
        assert rows[0].entry_type == comment_aggregation.ENTRY_TYPE_COMMENT
        assert rows[0].content == 'approved comment'
        assert rows[0].created == datetime(2024, 3, 10, 10, 0, 0)
        assert rows[0].rating == 4
        assert rows[1].entry_type == comment_aggregation.ENTRY_TYPE_REPLY
        assert rows[1].content == 'approved reply'
        assert rows[1].created == datetime(2024, 3, 10, 11, 0, 0)
        assert rows[1].rating == 0

    def test_get_comments_outputs_each_reply_on_its_own_row(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        parent = _register_resource_comment(
            res['id'],
            content='approved comment',
            created=datetime(2024, 3, 10, 10, 0, 0),
        )
        _register_reply(
            parent.id,
            content='reply 1',
            created=datetime(2024, 3, 10, 11, 0, 0),
        )
        _register_reply(
            parent.id,
            content='reply 2',
            created=datetime(2024, 3, 10, 12, 0, 0),
        )

        session.commit()

        rows = comment_aggregation.get_comments(org['name'])

        assert len(rows) == 3
        assert rows[0].entry_type == comment_aggregation.ENTRY_TYPE_COMMENT
        assert rows[0].content == 'approved comment'
        assert rows[0].rating == 4
        assert rows[1].entry_type == comment_aggregation.ENTRY_TYPE_REPLY
        assert rows[1].content == 'reply 1'
        assert rows[1].created == datetime(2024, 3, 10, 11, 0, 0)
        assert rows[1].rating == 0
        assert rows[2].entry_type == comment_aggregation.ENTRY_TYPE_REPLY
        assert rows[2].content == 'reply 2'
        assert rows[2].created == datetime(2024, 3, 10, 12, 0, 0)
        assert rows[2].rating == 0

    def test_get_comments_includes_comment_without_reply(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        _register_resource_comment(
            res['id'],
            content='comment only',
            created=datetime(2024, 3, 10, 10, 0, 0),
        )

        session.commit()

        rows = comment_aggregation.get_comments(org['name'])

        assert len(rows) == 1
        assert rows[0].entry_type == comment_aggregation.ENTRY_TYPE_COMMENT
        assert rows[0].content == 'comment only'
        assert rows[0].rating == 4

    def test_get_comments_uses_zero_when_rating_is_missing(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        _register_resource_comment(
            res['id'],
            content='comment without rating',
            created=datetime(2024, 3, 10, 10, 0, 0),
            rating=None,
        )

        session.commit()

        rows = comment_aggregation.get_comments(org['name'])

        assert len(rows) == 1
        assert rows[0].rating == 0

    def test_get_comments_orders_by_resource_and_comment_created(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res_a = factories.Resource(package_id=ds['id'])
        res_b = factories.Resource(package_id=ds['id'])

        parent_a = _register_resource_comment(
            res_a['id'],
            content='resource a comment',
            created=datetime(2024, 3, 10, 10, 0, 0),
        )
        _register_reply(
            parent_a.id,
            content='resource a reply',
            created=datetime(2024, 3, 10, 11, 0, 0),
        )
        _register_resource_comment(
            res_b['id'],
            content='resource b comment',
            created=datetime(2024, 3, 10, 9, 0, 0),
        )

        session.commit()

        rows = comment_aggregation.get_comments(org['name'])

        assert len(rows) == 3
        assert rows[0].entry_type == comment_aggregation.ENTRY_TYPE_COMMENT
        assert rows[0].content == 'resource a comment'
        assert rows[1].entry_type == comment_aggregation.ENTRY_TYPE_REPLY
        assert rows[1].content == 'resource a reply'
        assert rows[2].entry_type == comment_aggregation.ENTRY_TYPE_COMMENT
        assert rows[2].content == 'resource b comment'

    def test_get_monthly_comments_includes_comment_when_reply_is_in_period(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        parent = _register_resource_comment(
            res['id'],
            content='february comment',
            created=datetime(2024, 2, 15, 10, 0, 0),
        )
        _register_reply(
            parent.id,
            content='march reply',
            created=datetime(2024, 3, 15, 10, 0, 0),
        )

        session.commit()

        rows = comment_aggregation.get_monthly_comments(org['name'], '2024-03')

        assert len(rows) == 2
        assert rows[0].entry_type == comment_aggregation.ENTRY_TYPE_COMMENT
        assert rows[0].content == 'february comment'
        assert rows[1].entry_type == comment_aggregation.ENTRY_TYPE_REPLY
        assert rows[1].content == 'march reply'
        assert rows[1].created == datetime(2024, 3, 15, 10, 0, 0)
