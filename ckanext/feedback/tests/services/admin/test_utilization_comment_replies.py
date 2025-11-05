import uuid
from datetime import datetime

import pytest
from ckan import model
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_utilization_tables,
    drop_utilization_tables,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
    UtilizationCommentReply,
)
from ckanext.feedback.services.admin import (
    utilization_comment_replies as replies_service,
)

engine = model.repo.session.get_bind()


def _register_utilization(resource_id, approval=False):
    u = Utilization(
        id=str(uuid.uuid4()),
        resource_id=resource_id,
        title='util',
        url=None,
        description='desc',
        comment=0,
        approval=approval,
        approved=None,
        approval_user_id=None,
    )
    session.add(u)
    return u


def _register_utilization_comment(utilization_id, approval=False):
    uc = UtilizationComment(
        id=str(uuid.uuid4()),
        utilization_id=utilization_id,
        category=UtilizationCommentCategory.QUESTION,
        content='uc',
        created=datetime.now(),
        approval=approval,
        approved=None,
        approval_user_id=None,
        attached_image_filename=None,
    )
    session.add(uc)
    return uc


def _register_reply(
    utilization_comment_id, content='reply', approval=False, created=None
):
    r = UtilizationCommentReply(
        id=str(uuid.uuid4()),
        utilization_comment_id=utilization_comment_id,
        content=content,
        created=created or datetime.now(),
        approval=approval,
        approved=None,
        approval_user_id=None,
        creator_user_id=None,
    )
    session.add(r)
    return r


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestUtilizationCommentReplies:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        drop_utilization_tables(engine)
        create_utilization_tables(engine)

    def test_get_utilization_comment_replies_query_hit(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        u = _register_utilization(res['id'], approval=False)
        uc = _register_utilization_comment(u.id, approval=True)
        session.flush()
        r = _register_reply(uc.id, content='hello', approval=False)
        session.commit()

        org_list = [{'name': org['name'], 'title': org['title']}]
        rows = replies_service.get_utilization_comment_replies_query(org_list).all()

        assert len(rows) == 1
        row = rows[0]
        assert row.group_name == org['name']
        assert row.package_name == ds['name']
        assert row.package_title == ds['title']
        assert row.owner_org == ds['owner_org']
        assert row.resource_id == res['id']
        assert row.resource_name == res['name']
        assert row.utilization_id == u.id
        assert row.feedback_type == 'utilization_comment_reply'
        assert row.comment_id == r.id
        assert row.content == 'hello'
        assert isinstance(row.created, datetime)
        assert row.is_approved is False

    def test_get_utilization_comment_replies_query_no_match(self):
        org = factories.Organization()
        org_list = [{'name': org['name'], 'title': org['title']}]
        rows = replies_service.get_utilization_comment_replies_query(org_list).all()
        assert rows == []

    def test_get_simple_utilization_comment_replies_query_hit(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        u = _register_utilization(res['id'], approval=False)
        uc = _register_utilization_comment(u.id, approval=True)
        session.flush()
        _ = _register_reply(uc.id, content='simple', approval=False)
        session.commit()

        org_list = [{'name': org['name'], 'title': org['title']}]
        rows = replies_service.get_simple_utilization_comment_replies_query(
            org_list
        ).all()

        assert len(rows) == 1
        row = rows[0]
        assert row.group_name == org['name']
        assert row.feedback_type == 'utilization_comment_reply'
        assert row.is_approved is False

    def test_get_simple_utilization_comment_replies_query_no_match(self):
        org = factories.Organization()
        org_list = [{'name': org['name'], 'title': org['title']}]
        rows = replies_service.get_simple_utilization_comment_replies_query(
            org_list
        ).all()
        assert rows == []

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_approve_utilization_comment_replies_parent_approved_and_unapproved(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        u_ok = _register_utilization(res['id'], approval=False)
        uc_ok = _register_utilization_comment(u_ok.id, approval=True)

        u_ng = _register_utilization(res['id'], approval=False)
        uc_ng = _register_utilization_comment(u_ng.id, approval=False)

        session.flush()
        r_ok = _register_reply(uc_ok.id, approval=False)
        r_ng = _register_reply(uc_ng.id, approval=False)

        session.commit()

        updated = replies_service.approve_utilization_comment_replies(
            [r_ok.id, r_ng.id], approval_user_id=None
        )
        assert updated == 1

        session.expire_all()

        ok = session.query(UtilizationCommentReply).get(r_ok.id)
        ng = session.query(UtilizationCommentReply).get(r_ng.id)

        assert ok.approval is True
        assert ok.approved == datetime(2000, 1, 2, 3, 4)
        assert ok.approval_user_id is None

        assert ng.approval is False
        assert ng.approved is None

    def test_approve_utilization_comment_replies_all_parents_unapproved(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        u = _register_utilization(res['id'], approval=False)
        uc = _register_utilization_comment(u.id, approval=False)
        session.flush()
        r = _register_reply(uc.id, approval=False)
        session.commit()

        updated = replies_service.approve_utilization_comment_replies(
            [r.id], approval_user_id=None
        )
        assert updated == 0

        session.expire_all()
        row = session.query(UtilizationCommentReply).get(r.id)
        assert row.approval is False
        assert row.approved is None

    def test_approve_utilization_comment_replies_empty_input(self):
        updated = replies_service.approve_utilization_comment_replies(
            [], approval_user_id=None
        )
        assert updated == 0

    def test_delete_utilization_comment_replies(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        u = _register_utilization(res['id'], approval=False)
        uc = _register_utilization_comment(u.id, approval=False)
        session.flush()
        r = _register_reply(uc.id, approval=False)
        session.commit()

        replies_service.delete_utilization_comment_replies([r.id])

        exists = session.query(UtilizationCommentReply).get(r.id)
        assert exists is None

    def test_delete_utilization_comment_replies_empty_input(self):
        org = factories.Organization()
        ds = factories.Dataset(owner_org=org['id'])
        res = factories.Resource(package_id=ds['id'])

        u = _register_utilization(res['id'], approval=False)
        uc = _register_utilization_comment(u.id, approval=False)
        session.flush()
        r = _register_reply(uc.id, approval=False)
        session.commit()

        replies_service.delete_utilization_comment_replies([])

        still = session.query(UtilizationCommentReply).get(r.id)
        assert still is not None
