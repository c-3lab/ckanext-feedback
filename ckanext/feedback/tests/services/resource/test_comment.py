from unittest.mock import MagicMock, call, patch

import pytest
from ckan import model
from ckan.model.package import Package
from ckan.model.resource import Resource
from ckan.model.user import User
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentCategory,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.services.resource.comment import (
    approve_resource_comment,
    create_reply,
    create_resource_comment,
    get_attached_image_path,
    get_comment_attached_image_files,
    get_comment_reply,
    get_cookie,
    get_resource,
    get_resource_comment,
    get_resource_comment_categories,
    get_resource_comments,
    get_upload_destination,
)


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestComments:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = model.meta.engine
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_resource(self):
        organization_dict = factories.Organization(
            name='org_name',
        )
        package = factories.Dataset(owner_org=organization_dict['id'])
        resource = factories.Resource(package_id=package['id'])
        session.commit()
        assert get_resource(resource['id'])
        assert get_resource(resource['id']).organization_id == package['id']
        assert get_resource(resource['id']).organization_name == "org_name"

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

    def test_get_resource_comments(self):
        assert not get_resource_comments()
        organization = factories.Organization()
        package = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=package['id'])
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

    def test_create_resource_comment(self):
        pass

    def test_get_resource_comment_categories(self):
        assert get_resource_comment_categories() == ResourceCommentCategory

    def test_approve_resource_comment(self):
        resource = factories.Resource()
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

    def test_create_reply(self):
        resource = factories.Resource()
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        comment_id = session.query(ResourceComment).first().id
        user_id = session.query(User).first().id
        assert not get_comment_reply(comment_id)
        create_reply(comment_id, 'test_reply', user_id)
        session.commit()
        assert get_comment_reply(comment_id)

    def test_get_cookie(self):
        resource = factories.Resource()
        assert not get_cookie(resource['id'])

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

    @patch('ckanext.feedback.services.resource.comment.session')
    def test_get_comment_attached_image_files(self, mock_session):
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
            ('attached_image_filename1',),
            ('attached_image_filename2',),
        ]
        mock_session.query.return_value = mock_query

        get_comment_attached_image_files()

        mock_session.query.assert_called_once_with(
            ResourceComment.attached_image_filename
        )
        assert mock_query.filter.call_count == 1
        mock_query.all.assert_called_once()
