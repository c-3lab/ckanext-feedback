from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest
from ckan import model
from ckan.model.package import Package
from ckan.model.resource import Resource
from ckan.model.user import User

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentCategory,
    ResourceCommentReply,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.types import (
    MoralCheckAction,
    ResourceCommentResponseStatus,
)
from ckanext.feedback.services.resource.comment import (
    approve_reply,
    approve_resource_comment,
    create_reply,
    create_resource_comment,
    create_resource_comment_moral_check_log,
    create_resource_comment_reactions,
    get_attached_image_path,
    get_comment_attached_image_files,
    get_comment_replies,
    get_comment_replies_for_display,
    get_comment_reply,
    get_resource,
    get_resource_comment,
    get_resource_comment_categories,
    get_resource_comment_moral_check_logs,
    get_resource_comment_reactions,
    get_resource_comments,
    get_upload_destination,
    update_resource_comment_reactions,
)


@pytest.mark.usefixtures('with_plugins', 'with_request_context')
@pytest.mark.db_test
class TestComments:
    def test_get_resource(self, organization, dataset, resource):
        row = get_resource(resource['id'])
        assert row
        assert row.organization_id == dataset['id']
        assert row.organization_name == organization['name']

    @patch('ckanext.feedback.services.resource.comment.session')
    def test_get_resource_comment(self, mock_session):
        comment_id = 'comment_id'
        resource_id = 'resource_id'
        approval = True
        attached_image_filename = 'attached_image_filename'
        owner_orgs = ['org1', 'org2']

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.first.return_value = 'mock_comment'
        mock_session.query.return_value = mock_query

        get_resource_comment(
            comment_id, resource_id, approval, attached_image_filename, owner_orgs
        )

        mock_session.query.assert_called_once_with(ResourceComment)
        assert mock_query.filter.call_count == 5
        mock_query.join.assert_has_calls(
            [
                call(Resource),
                call(Package),
            ]
        )
        mock_query.first.assert_called_once()

    @patch('ckanext.feedback.services.resource.comment.session')
    def test_get_resource_comment_with_none_args(self, mock_session):
        comment_id = 'comment_id'

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.first.return_value = 'mock_comment'
        mock_session.query.return_value = mock_query

        get_resource_comment(comment_id)

        mock_session.query.assert_called_once_with(ResourceComment)
        assert mock_query.filter.call_count == 1
        mock_query.join.assert_not_called()
        mock_query.first.assert_called_once()

    def test_get_resource_comments(self, organization, resource):
        assert not get_resource_comments()

        limit = 20
        offset = 0

        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        session.commit()
        assert get_resource_comments()
        assert get_resource_comments(resource['id'])
        assert get_resource_comments(resource['id'], None, [organization['id']])
        assert not get_resource_comments('test')
        assert not get_resource_comments(resource['id'], True)
        assert get_resource_comments(
            limit=limit,
            offset=offset,
        )

    def test_get_resource_comment_categories(self):
        assert get_resource_comment_categories() == ResourceCommentCategory

    def test_approve_resource_comment(self, resource):
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        session.commit()
        comment_id = session.query(ResourceComment).first().id
        user_id = session.query(User).first().id

        assert not get_resource_comments(resource['id'])[0].approval

        approve_resource_comment(comment_id, user_id)
        session.commit()
        assert get_resource_comments(resource['id'])[0].approval

    def test_get_comment_reply(self):
        pass

    def test_create_reply(self, resource):
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        comment_id = session.query(ResourceComment).first().id
        user_id = session.query(User).first().id
        assert not get_comment_reply(comment_id)
        create_reply(comment_id, 'test_reply', user_id)
        session.commit()
        assert get_comment_reply(comment_id)


@pytest.mark.db_test
class TestResourceComment:
    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_create_resource_comment(self, resource):
        create_resource_comment(
            resource['id'],
            ResourceCommentCategory.REQUEST,
            'test_content',
            3,
            'test_attached_image.jpg',
        )
        session.commit()

        rows = get_resource_comments(resource['id'])
        resource_comment = rows[0]
        resource_comment_reactions = get_resource_comment_reactions(resource_comment.id)

        assert resource_comment.resource_id == resource['id']
        assert resource_comment.category == ResourceCommentCategory.REQUEST
        assert resource_comment.content == 'test_content'
        assert resource_comment.rating == 3
        assert resource_comment.attached_image_filename == 'test_attached_image.jpg'
        assert resource_comment.created == datetime(2024, 1, 1, 15, 0, 0)
        assert resource_comment_reactions.resource_comment_id == resource_comment.id
        assert (
            resource_comment_reactions.response_status
            == ResourceCommentResponseStatus.STATUS_NONE
        )
        assert resource_comment_reactions.admin_liked is False
        assert resource_comment_reactions.created == datetime(2024, 1, 1, 15, 0, 0)
        assert resource_comment_reactions.updated is None
        assert resource_comment_reactions.updater_user_id is None


@pytest.mark.db_test
class TestResourceCommentReactions:
    def test_get_resource_comment_reactions_exists_returns_reaction(
        self, resource_comment
    ):
        create_resource_comment_reactions(
            resource_comment_id=resource_comment.id,
            response_status=ResourceCommentResponseStatus.STATUS_NONE,
            admin_liked=False,
            updater_user_id=None,
        )
        session.flush()

        result = get_resource_comment_reactions(resource_comment.id)

        assert result is not None
        assert result.resource_comment_id == resource_comment.id
        assert result.response_status is ResourceCommentResponseStatus.STATUS_NONE
        assert result.admin_liked is False
        assert result.updater_user_id is None

    def test_get_resource_comment_reactions_not_exists_returns_none(
        self, resource_comment
    ):
        result = get_resource_comment_reactions(resource_comment.id)

        assert result is None

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_create_resource_comment_reactions(self, user, resource_comment):
        create_resource_comment_reactions(
            resource_comment_id=resource_comment.id,
            response_status=ResourceCommentResponseStatus.COMPLETED,
            admin_liked=True,
            updater_user_id=user['id'],
        )
        session.flush()

        result = get_resource_comment_reactions(resource_comment.id)

        assert result.resource_comment_id == resource_comment.id
        assert result.response_status is ResourceCommentResponseStatus.COMPLETED
        assert result.admin_liked is True
        assert result.created == datetime(2024, 1, 1, 15, 0, 0)
        assert result.updated == datetime(2024, 1, 1, 15, 0, 0)
        assert result.updater_user_id == user['id']

    def test_update_resource_comment_reactions(
        self,
        user,
        resource_comment_reactions,
    ):
        assert (
            resource_comment_reactions.response_status
            is ResourceCommentResponseStatus.STATUS_NONE
        )
        assert resource_comment_reactions.admin_liked is False
        assert resource_comment_reactions.updater_user_id is None

        update_resource_comment_reactions(
            reactions=resource_comment_reactions,
            response_status=ResourceCommentResponseStatus.COMPLETED,
            admin_liked=True,
            updater_user_id=user['id'],
        )
        session.flush()

        result = get_resource_comment_reactions(
            resource_comment_reactions.resource_comment_id
        )

        assert result.response_status is ResourceCommentResponseStatus.COMPLETED
        assert result.admin_liked is True
        assert result.updater_user_id == user['id']


class TestAttachedImageConfig:
    @patch('ckanext.feedback.services.resource.comment.get_upload_destination')
    @patch('ckanext.feedback.services.resource.comment.get_uploader')
    def test_get_attached_image_path(
        self, mock_get_uploader, mock_get_upload_destination
    ):
        attached_image_filename = 'attached_image_filename'

        mock_get_upload_destination.return_value = '/test/upload/path'

        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        get_attached_image_path(attached_image_filename)

        mock_get_upload_destination.assert_called_once()
        mock_get_uploader.assert_called_once()

    def test_get_upload_destination(self):
        assert get_upload_destination() == 'feedback_resouce_comment'


@pytest.mark.db_test
class TestAttachedImageService:
    def test_get_comment_attached_image_files(self, resource_comment):
        result = get_comment_attached_image_files()

        assert result == ['test_attached_image.jpg']


@pytest.mark.db_test
class TestResourceCommentMoralCheckLog:
    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_create_resource_comment_moral_check_log(self, resource):
        resource_id = resource['id']
        action = MoralCheckAction.INPUT_SELECTED
        input_comment = 'test_input_comment'
        suggested_comment = 'test_suggested_comment'
        output_comment = 'test_output_comment'

        create_resource_comment_moral_check_log(
            resource_id,
            action,
            input_comment,
            suggested_comment,
            output_comment,
        )
        session.flush()

        results = get_resource_comment_moral_check_logs()

        assert results is not None
        assert results[0].resource_id == resource_id
        assert results[0].action == action
        assert results[0].input_comment == input_comment
        assert results[0].suggested_comment == suggested_comment
        assert results[0].output_comment == output_comment
        assert results[0].timestamp == datetime(2024, 1, 1, 15, 0, 0)

    def test_get_resource_comment_moral_check_logs(
        self, resource_comment_moral_check_log
    ):
        results = get_resource_comment_moral_check_logs()

        assert results is not None
        assert results[0].id == resource_comment_moral_check_log.id
        assert results[0].resource_id == resource_comment_moral_check_log.resource_id
        assert results[0].action == resource_comment_moral_check_log.action
        assert (
            results[0].input_comment == resource_comment_moral_check_log.input_comment
        )
        assert (
            results[0].suggested_comment
            == resource_comment_moral_check_log.suggested_comment
        )
        assert (
            results[0].output_comment == resource_comment_moral_check_log.output_comment
        )
        assert results[0].timestamp == resource_comment_moral_check_log.timestamp

    def test_get_comment_replies_filters_and_order(self, resource):
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        session.commit()
        parent = session.query(ResourceComment).first()

        r1 = ResourceCommentReply(
            resource_comment_id=parent.id,
            content='older',
            created=datetime(2020, 1, 1),
            approval=False,
        )
        r2 = ResourceCommentReply(
            resource_comment_id=parent.id,
            content='newer',
            created=datetime(2021, 1, 1),
            approval=True,
        )
        session.add_all([r1, r2])
        session.commit()

        replies = get_comment_replies(parent.id)
        assert [r.content for r in replies] == ['older', 'newer']

        replies_only_approved = get_comment_replies(parent.id, approval=True)
        assert [r.content for r in replies_only_approved] == ['newer']

    def test_approve_reply_not_found(self):
        with pytest.raises(ValueError):
            approve_reply('non-exists-id', approval_user_id=None)

    def test_approve_reply_parent_not_found(self, resource):
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        session.commit()
        parent = session.query(ResourceComment).first()
        create_reply(parent.id, 'reply', None)
        session.commit()
        reply = session.query(ResourceCommentReply).first()

        from types import SimpleNamespace

        real_session = session

        class QueryRouter:
            def query(self, model_cls):
                if model_cls is ResourceComment:
                    return SimpleNamespace(get=lambda _id: None)
                return real_session.query(model_cls)

        from unittest.mock import patch

        with patch(
            'ckanext.feedback.services.resource.comment.session', new=QueryRouter()
        ):
            with pytest.raises(ValueError):
                approve_reply(reply.id, approval_user_id=None)

    def test_approve_reply_parent_not_approved(self, resource):
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        session.commit()
        parent = session.query(ResourceComment).first()
        create_reply(parent.id, 'reply', None)
        session.commit()
        reply = session.query(ResourceCommentReply).first()

        with pytest.raises(PermissionError):
            approve_reply(reply.id, approval_user_id=None)

    def test_approve_reply_success(self, resource):
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        session.commit()
        parent = session.query(ResourceComment).first()

        approve_resource_comment(parent.id, approval_user_id=None)
        session.commit()

        create_reply(parent.id, 'reply', None)
        session.commit()
        reply = session.query(ResourceCommentReply).first()

        approve_reply(reply.id, approval_user_id=None)
        session.commit()

        updated = session.query(ResourceCommentReply).get(reply.id)
        assert updated.approval is True
        assert updated.approval_user_id is None
        assert isinstance(updated.approved, datetime)

    def test_get_comment_replies_for_display_non_admin(self, dataset, resource):
        from unittest.mock import patch as _patch

        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        session.commit()
        parent = session.query(ResourceComment).first()

        r1 = ResourceCommentReply(
            resource_comment_id=parent.id, content='u', approval=False
        )
        r2 = ResourceCommentReply(
            resource_comment_id=parent.id, content='a', approval=True
        )
        session.add_all([r1, r2])
        session.commit()

        with _patch(
            'ckanext.feedback.services.resource.comment.current_user', new=object()
        ):
            rows = get_comment_replies_for_display(parent.id, dataset['owner_org'])
        assert [r.content for r in rows] == ['a']

    @patch('flask_login.utils._get_user')
    def test_get_comment_replies_for_display_sysadmin(
        self, current_user, sysadmin, dataset, resource
    ):
        user_obj = model.User.get(sysadmin['id'])
        current_user.return_value = user_obj
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        session.commit()
        parent = session.query(ResourceComment).first()

        r1 = ResourceCommentReply(
            resource_comment_id=parent.id, content='u', approval=False
        )
        r2 = ResourceCommentReply(
            resource_comment_id=parent.id, content='a', approval=True
        )
        session.add_all([r1, r2])
        session.commit()

        rows = get_comment_replies_for_display(parent.id, dataset['owner_org'])
        assert sorted([r.content for r in rows]) == ['a', 'u']

    @patch('flask_login.utils._get_user')
    def test_get_comment_replies_for_display_org_admin(
        self, current_user, user, organization, dataset, resource
    ):
        user_obj = model.User.get(user['id'])
        current_user.return_value = user_obj

        organization_obj = model.Group.get(organization['id'])
        member = model.Member(
            group=organization_obj,
            group_id=organization_obj.id,
            table_id=user_obj.id,
            capacity='admin',
            table_name='user',
        )
        model.Session.add(member)
        model.Session.commit()

        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        session.commit()
        parent = session.query(ResourceComment).first()

        r1 = ResourceCommentReply(
            resource_comment_id=parent.id, content='u', approval=False
        )
        r2 = ResourceCommentReply(
            resource_comment_id=parent.id, content='a', approval=True
        )
        session.add_all([r1, r2])
        session.commit()

        rows = get_comment_replies_for_display(parent.id, dataset['owner_org'])
        assert sorted([r.content for r in rows]) == ['a', 'u']

    def test_get_resource_comment_replies_query(self, organization):
        from ckanext.feedback.services.admin import resource_comments as rc

        org_list = [{'name': organization['name'], 'title': organization['title']}]
        q = rc.get_resource_comment_replies_query(org_list)
        s = str(q.statement)
        assert "resource_comment_reply" in s

    def test_get_simple_resource_comment_replies_query(self, organization):
        from ckanext.feedback.services.admin import resource_comments as rc

        org_list = [{'name': organization['name'], 'title': organization['title']}]

        q = rc.get_simple_resource_comment_replies_query(org_list)
        s = str(q.statement)
        assert "resource_comment_reply" in s

    def test_create_reply_with_attached_image(self, resource):
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'parent', 1)
        session.commit()
        parent = session.query(ResourceComment).first()
        user_id = session.query(model.User).first().id

        create_reply(parent.id, 'reply with image', user_id, 'reply_img.jpg')
        session.commit()
        reply = session.query(ResourceCommentReply).first()
        assert reply.attached_image_filename == 'reply_img.jpg'
