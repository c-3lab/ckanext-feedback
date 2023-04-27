from unittest.mock import patch

import pytest
from ckan import model
from ckan.logic import get_action
from ckan.model import User
from ckan.tests import factories
from flask import Flask, g

import ckanext.feedback.services.resource.comment as comment_service
from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.resource import ResourceController
from ckanext.feedback.models.session import session

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestResourceController:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)

    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.request')
    def test_comment(self, mock_request, mock_render):
        dataset = factories.Dataset()
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        resource = factories.Resource(package_id=dataset['id'])
        resource_id = resource['id']
        user_env = {'REMOTE_USER': user.name}

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            ResourceController.comment(resource_id)

        approval = True
        resource = comment_service.get_resource(resource_id)
        comments = comment_service.get_resource_comments(resource_id, approval)
        categories = comment_service.get_resource_comment_categories()
        cookie = comment_service.get_cookie(resource_id)
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(context, {'id': resource.package_id})

        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': resource,
                'pkg_dict': package,
                'comments': comments,
                'categories': categories,
                'cookie': cookie,
            },
        )

    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.request')
    def test_comment_without_user(self, mock_request, mock_render):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        resource_id = resource['id']

        with self.app.test_request_context(path='/'):
            g.userobj = None
            ResourceController.comment(resource_id)

        approval = False
        resource = comment_service.get_resource(resource_id)
        comments = comment_service.get_resource_comments(resource_id, approval)
        categories = comment_service.get_resource_comment_categories()
        cookie = comment_service.get_cookie(resource_id)
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(context, {'id': resource.package_id})

        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': resource,
                'pkg_dict': package,
                'comments': comments,
                'categories': categories,
                'cookie': cookie,
            },
        )

    @patch('ckanext.feedback.controllers.resource.request')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_success')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.url_for')
    @patch('ckanext.feedback.controllers.resource.redirect')
    @patch('ckanext.feedback.controllers.resource.make_response')
    def test_create_comment(
        self,
        mock_make_response,
        mock_redirect,
        mock_url_for,
        mock_session_commit,
        mock_flash_success,
        mock_comment_service,
        mock_summary_service,
        mock_request,
    ):
        resource_id = 'resource id'
        category = 'category'
        comment_content = 'content'
        rating = '1'
        mock_request.form.get.side_effect = [
            comment_content,
            comment_content,
            category,
            rating,
            rating,
        ]

        mock_url_for.return_value = 'resource comment'
        resp = ResourceController.create_comment(resource_id)

        mock_comment_service.create_resource_comment.assert_called_once_with(
            resource_id, category, comment_content, int(rating)
        )
        mock_summary_service.create_resource_summary.assert_called_once_with(
            resource_id
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )
        mock_redirect.assert_called_once_with('resource comment')
        mock_make_response.assert_called_once_with(mock_redirect())
        resp.set_cookie.assert_called_once_with(resource_id, 'alreadyPosted')

    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.request')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_success')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.url_for')
    @patch('ckanext.feedback.controllers.resource.redirect')
    @patch('ckanext.feedback.controllers.resource.make_response')
    def test_create_comment_without_category_content(
        self,
        mock_make_response,
        mock_redirect,
        mock_url_for,
        mock_session_commit,
        mock_flash_success,
        mock_comment_service,
        mock_summary_service,
        mock_request,
        mock_toolkit_abort,
    ):
        resource_id = 'resource id'
        mock_request.form.get.side_effect = [
            None,
            None,
        ]
        ResourceController.create_comment(resource_id)
        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.resource.request')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.url_for')
    @patch('ckanext.feedback.controllers.resource.redirect')
    def test_approve_comment(
        self,
        mock_redirect,
        mock_url_for,
        mock_session_commit,
        mock_comment_service,
        mock_summary_service,
        mock_request,
    ):
        resource_id = 'resource id'
        resource_comment_id = 'resource comment id'

        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user

        mock_request.form.get.side_effect = [resource_comment_id]

        mock_url_for.return_value = 'resource comment url'
        ResourceController.approve_comment(resource_id)

        mock_comment_service.approve_resource_comment.assert_called_once_with(
            resource_comment_id, user.id
        )
        mock_summary_service.refresh_resource_summary.assert_called_once_with(
            resource_id
        )
        mock_session_commit.assert_called_once()
        mock_url_for.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )

        mock_redirect.assert_called_once_with('resource comment url')

    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.request')
    def test_approve_comment_without_resource_comment_id(
        self,
        mock_request,
        mock_comment_service,
        mock_summary_service,
        mock_toolkit_abort,
    ):
        resource_id = 'resource id'

        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user

        mock_request.form.get.side_effect = [None]

        ResourceController.approve_comment(resource_id)
        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.resource.request')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.url_for')
    @patch('ckanext.feedback.controllers.resource.redirect')
    def test_reply(
        self,
        mock_redirect,
        mock_url_for,
        mock_session_commit,
        mock_comment_service,
        mock_summary_service,
        mock_request,
    ):
        resource_id = 'resource id'
        resource_comment_id = 'resource comment id'
        reply_content = 'reply content'

        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user

        mock_request.form.get.side_effect = [
            resource_comment_id,
            reply_content,
        ]

        mock_url_for.return_value = 'resource comment url'
        ResourceController.reply(resource_id)

        mock_comment_service.create_reply.assert_called_once_with(
            resource_comment_id, reply_content, user.id
        )
        mock_session_commit.assert_called_once()
        mock_url_for.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )

        mock_redirect.assert_called_once_with('resource comment url')

    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.request')
    def test_reply_without_resource_comment_id(
        self,
        mock_request,
        mock_comment_service,
        mock_summary_service,
        mock_toolkit_abort,
    ):
        resource_id = 'resource id'

        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user

        mock_request.form.get.side_effect = [
            None,
            None,
        ]

        ResourceController.reply(resource_id)
        mock_toolkit_abort.assert_called_once_with(400)
