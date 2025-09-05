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
from ckanext.feedback.services.admin import resource_comment_replies as replies_service

engine = model.repo.session.get_bind()


def _register_resource_comment(resource_id, approval=False):
    rc = ResourceComment(
        id=str(uuid.uuid4()),
        resource_id=resource_id,
        category=ResourceCommentCategory.QUESTION,
        content='parent comment',
        rating=None,
        created=datetime.now(),
        approval=approval,
        approved=None,
        approval_user_id=None,
    )
    session.add(rc)
    return rc


def _register_reply(resource_comment_id, content='reply', created=None, approval=False):
    rr = ResourceCommentReply(
        id=str(uuid.uuid4()),
        resource_comment_id=resource_comment_id,
        content=content,
        created=created or datetime.now(),
        approval=approval,
        approved=None,
        approval_user_id=None,
    )
    session.add(rr)
    return rr


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestResourceCommentReplies:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        drop_resource_tables(engine)
        create_resource_tables(engine)

    def test_get_resource_comment_replies_query(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        parent = _register_resource_comment(res['id'], approval=False)
        reply = _register_reply(parent.id, content='hello')

        session.commit()

        org_list = [{'name': org['name'], 'title': org['title']}]
        q = replies_service.get_resource_comment_replies_query(org_list)
        rows = q.all()

        assert len(rows) == 1
        row = rows[0]
        assert row.group_name == org['name']
        assert row.package_name == ds['name']
        assert row.package_title == ds['title']
        assert row.resource_id == res['id']
        assert row.resource_name == res['name']
        assert row.utilization_id is None
        assert row.feedback_type == 'resource_comment_reply'
        assert row.comment_id == reply.id
        assert row.content == 'hello'
        assert isinstance(row.created, datetime)
        assert row.is_approved is False

    def test_get_resource_comment_replies_query_filters_by_org(self):

        org_a = factories.Organization()
        ds_a = factories.Dataset(owner_org=org_a['id'])
        res_a = factories.Resource(package_id=ds_a['id'])
        parent_a = _register_resource_comment(res_a['id'], approval=False)
        _ = _register_reply(parent_a.id, content='A')

        org_b = factories.Organization()
        ds_b = factories.Dataset(owner_org=org_b['id'])
        res_b = factories.Resource(package_id=ds_b['id'])
        parent_b = _register_resource_comment(res_b['id'], approval=False)
        _ = _register_reply(parent_b.id, content='B')

        session.commit()

        org_list = [{'name': org_a['name'], 'title': org_a['title']}]
        rows = replies_service.get_resource_comment_replies_query(org_list).all()
        assert len(rows) == 1
        assert rows[0].group_name == org_a['name']
        assert rows[0].content == 'A'

    def test_get_simple_resource_comment_replies_query(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        parent = _register_resource_comment(res['id'], approval=True)
        _ = _register_reply(parent.id, content='simple', approval=False)
        session.commit()

        org_list = [{'name': org['name'], 'title': org['title']}]
        rows = replies_service.get_simple_resource_comment_replies_query(org_list).all()

        assert len(rows) == 1
        row = rows[0]
        assert row.group_name == org['name']
        assert row.feedback_type == 'resource_comment_reply'
        assert row.is_approved is False

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_approve_resource_comment_replies_parent_approved_and_unapproved(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        parent_ok = _register_resource_comment(res['id'], approval=True)
        reply_ok = _register_reply(parent_ok.id)

        parent_ng = _register_resource_comment(res['id'], approval=False)
        reply_ng = _register_reply(parent_ng.id)

        session.commit()

        updated = replies_service.approve_resource_comment_replies(
            [reply_ok.id, reply_ng.id], approval_user_id=None
        )
        assert updated == 1

        session.expire_all()

        ok = session.query(ResourceCommentReply).get(reply_ok.id)
        ng = session.query(ResourceCommentReply).get(reply_ng.id)

        assert ok.approval is True
        assert ok.approved == datetime(2000, 1, 2, 3, 4)
        assert ok.approval_user_id is None

        assert ng.approval is False
        assert ng.approved is None

    def test_approve_resource_comment_replies_empty_input(self):
        updated = replies_service.approve_resource_comment_replies(
            [], approval_user_id=None
        )
        assert updated == 0

    def test_delete_resource_comment_replies(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        parent = _register_resource_comment(res['id'], approval=False)
        reply = _register_reply(parent.id)
        session.commit()

        replies_service.delete_resource_comment_replies([reply.id])

        exists = session.query(ResourceCommentReply).get(reply.id)
        assert exists is None

    def test_get_resource_comment_replies_query_no_match(self):

        org = factories.Organization()
        org_list = [{'name': org['name'], 'title': org['title']}]
        rows = replies_service.get_resource_comment_replies_query(org_list).all()
        assert rows == []

    def test_get_simple_resource_comment_replies_query_no_match(self):

        org = factories.Organization()
        org_list = [{'name': org['name'], 'title': org['title']}]
        rows = replies_service.get_simple_resource_comment_replies_query(org_list).all()
        assert rows == []

    def test_approve_resource_comment_replies_all_parents_unapproved(self):

        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        parent = _register_resource_comment(res['id'], approval=False)
        reply = _register_reply(parent.id)
        session.commit()

        updated = replies_service.approve_resource_comment_replies(
            [reply.id], approval_user_id=None
        )
        assert updated == 0

        session.expire_all()
        row = session.query(ResourceCommentReply).get(reply.id)
        assert row.approval is False
        assert row.approved is None

    def test_delete_resource_comment_replies_empty_input(self):

        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        parent = _register_resource_comment(res['id'], approval=False)
        reply = _register_reply(parent.id)
        session.commit()

        replies_service.delete_resource_comment_replies([])

        exists = session.query(ResourceCommentReply).get(reply.id)
        assert exists is not None
