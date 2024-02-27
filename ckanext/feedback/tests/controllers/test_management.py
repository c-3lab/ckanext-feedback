from unittest.mock import MagicMock, patch

import pytest
import six
from ckan import model
from ckan.common import _
from ckan.model import User
from ckan.tests import factories
from flask import Flask, g
from flask_babel import Babel

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.management import ManagementController

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestManagementController:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)

    @patch('ckanext.feedback.controllers.management.toolkit.render')
    @patch('ckanext.feedback.controllers.management.request')
    @patch('ckanext.feedback.controllers.management.utilization_detail_service')
    @patch('ckanext.feedback.controllers.management.resource_comment_service')
    def test_comments_with_sysadmin(
        self,
        mock_comment_service,
        mock_detail_service,
        mock_request,
        mock_render,
    ):
        categories = ['category']
        utilization_comments = ['utilization_comment']
        resource_comments = ['resource_comment']
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        mock_comment_service.get_resource_comments.return_value = resource_comments
        mock_detail_service.get_utilization_comment_categories.return_value = categories
        mock_detail_service.get_utilization_comments.return_value = utilization_comments
        mock_request.args.get.return_value = 'utilization-comments'

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            ManagementController.comments()

        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_utilization_comments.assert_called_once()
        mock_comment_service.get_resource_comments.assert_called_once()
        mock_request.args.get.assert_called_once_with('tab', 'utilization-comments')

        mock_render.assert_called_once_with(
            'management/comments.html',
            {
                'categories': categories,
                'utilization_comments': utilization_comments,
                'resource_comments': resource_comments,
                'tab': 'utilization-comments',
            },
        )

    @patch('ckanext.feedback.controllers.management.toolkit.render')
    @patch('ckanext.feedback.controllers.management.request')
    @patch('ckanext.feedback.controllers.management.utilization_detail_service')
    @patch('ckanext.feedback.controllers.management.resource_comment_service')
    def test_comments_with_org_admin(
        self,
        mock_comment_service,
        mock_detail_service,
        mock_request,
        mock_render,
    ):
        categories = ['category']
        utilization_comments = ['utilization_comment']
        resource_comments = ['resource_comment']
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        organization_dict = factories.Organization()
        organization = model.Group.get(organization_dict['id'])

        member = model.Member(
            group=organization,
            group_id=organization_dict['id'],
            table_id=user.id,
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()

        mock_comment_service.get_resource_comments.return_value = resource_comments
        mock_detail_service.get_utilization_comment_categories.return_value = categories
        mock_detail_service.get_utilization_comments.return_value = utilization_comments
        mock_request.args.get.return_value = 'utilization-comments'

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            ManagementController.comments()

        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_utilization_comments.assert_called_once()
        mock_comment_service.get_resource_comments.assert_called_once()
        mock_request.args.get.assert_called_once_with('tab', 'utilization-comments')

        mock_render.assert_called_once_with(
            'management/comments.html',
            {
                'categories': categories,
                'utilization_comments': utilization_comments,
                'resource_comments': resource_comments,
                'tab': 'utilization-comments',
            },
        )

    @patch('ckanext.feedback.controllers.management._')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.comments_service')
    @patch('ckanext.feedback.controllers.management.request')
    @patch('ckanext.feedback.controllers.management.c')
    def test_approve_bulk_utilization_comments(
        self,
        mock_c,
        mock_request,
        mock_comments_service,
        mock_session_commit,
        mock_flash_success,
        mock_url_for,
        mock_redirect,
        _,
    ):
        comments = ['comment']
        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_request.form.getlist.return_value = comments
        mock_comments_service.get_utilizations.return_value = utilizations
        mock_c.userobj.id = 'user_id'
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            response = ManagementController.approve_bulk_utilization_comments()

        mock_request.form.getlist.assert_called_once_with(
            'utilization-comments-checkbox'
        )
        mock_comments_service.get_utilizations.assert_called_once_with(comments)
        mock_comments_service.approve_utilization_comments.assert_called_once_with(
            comments, 'user_id'
        )
        mock_comments_service.refresh_utilizations_comments.assert_called_once_with(
            utilizations
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once_with(
            f'{len(comments)} ' + _('bulk approval completed.'),
            allow_html=True,
        )
        mock_url_for.assert_called_once_with(
            'management.comments', tab='utilization-comments'
        )
        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.request')
    def test_approve_bulk_utilization_comments_without_comment(
        self,
        mock_request,
        mock_url_for,
        mock_redirect,
    ):
        mock_request.form.getlist.return_value = None
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            response = ManagementController.approve_bulk_utilization_comments()

        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('ckanext.feedback.controllers.management._')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.comments_service')
    @patch('ckanext.feedback.controllers.management.request')
    @patch('ckanext.feedback.controllers.management.c')
    def test_approve_bulk_resource_comments(
        self,
        mock_c,
        mock_request,
        mock_comments_service,
        mock_session_commit,
        mock_flash_success,
        mock_url_for,
        mock_redirect,
        _,
    ):
        comments = ['comment']
        resource_comment_summary = MagicMock()
        resource_comment_summary.resource.package.owner_org = 'owner_org'
        resource_comment_summaries = [resource_comment_summary]

        mock_request.form.getlist.return_value = comments
        mock_comments_service.get_resource_comment_summaries.return_value = (
            resource_comment_summaries
        )
        mock_c.userobj.id = 'user_id'
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            response = ManagementController.approve_bulk_resource_comments()

        mock_request.form.getlist.assert_called_once_with('resource-comments-checkbox')
        mock_comments_service.get_resource_comment_summaries.assert_called_once_with(
            comments
        )
        mock_comments_service.approve_resource_comments.assert_called_once_with(
            comments, 'user_id'
        )
        mock_comments_service.refresh_resources_comments.assert_called_once_with(
            resource_comment_summaries
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once_with(
            f'{len(comments)} ' + _('bulk approval completed.'),
            allow_html=True,
        )
        mock_url_for.assert_called_once_with(
            'management.comments', tab='resource-comments'
        )
        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.request')
    def test_approve_bulk_resource_comments_without_comment(
        self,
        mock_request,
        mock_url_for,
        mock_redirect,
    ):
        mock_request.form.getlist.return_value = None
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            response = ManagementController.approve_bulk_resource_comments()

        mock_url_for.assert_called_once_with(
            'management.comments', tab='resource-comments'
        )
        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('ckanext.feedback.controllers.management._')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.comments_service')
    @patch('ckanext.feedback.controllers.management.request')
    def test_delete_bulk_utilization_comments(
        self,
        mock_request,
        mock_comments_service,
        mock_session_commit,
        mock_flash_success,
        mock_url_for,
        mock_redirect,
        _,
    ):
        comments = ['comment']
        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_request.form.getlist.return_value = comments
        mock_comments_service.get_utilizations.return_value = utilizations
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            response = ManagementController.delete_bulk_utilization_comments()

        mock_request.form.getlist.assert_called_once_with(
            'utilization-comments-checkbox'
        )
        mock_comments_service.get_utilizations.assert_called_once_with(comments)
        mock_comments_service.delete_utilization_comments.assert_called_once_with(
            comments
        )
        mock_comments_service.refresh_utilizations_comments.assert_called_once_with(
            utilizations
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once_with(
            f'{len(comments)} ' + _('bulk delete completed.'),
            allow_html=True,
        )
        mock_url_for.assert_called_once_with(
            'management.comments', tab='utilization-comments'
        )
        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.request')
    def test_delete_bulk_utilization_comments_without_comment(
        self,
        mock_request,
        mock_url_for,
        mock_redirect,
    ):
        mock_request.form.getlist.return_value = None
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            response = ManagementController.delete_bulk_utilization_comments()

        mock_url_for.assert_called_once_with(
            'management.comments', tab='utilization-comments'
        )
        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('ckanext.feedback.controllers.management._')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.comments_service')
    @patch('ckanext.feedback.controllers.management.request')
    def test_delete_bulk_resource_comments(
        self,
        mock_request,
        mock_comments_service,
        mock_session_commit,
        mock_flash_success,
        mock_url_for,
        mock_redirect,
        _,
    ):
        comments = ['comment1', 'comment2']
        resource_comment_summary1 = MagicMock()
        resource_comment_summary2 = MagicMock()
        resource_comment_summary1.resource.package.owner_org = 'owner_org1'
        resource_comment_summary2.resource.package.owner_org = 'owner_org2'
        resource_comment_summaries = [
            resource_comment_summary1,
            resource_comment_summary2,
        ]

        mock_request.form.getlist.return_value = comments
        mock_comments_service.get_resource_comment_summaries.return_value = (
            resource_comment_summaries
        )
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            response = ManagementController.delete_bulk_resource_comments()

        mock_request.form.getlist.assert_called_once_with('resource-comments-checkbox')
        mock_comments_service.get_resource_comment_summaries.assert_called_once_with(
            comments
        )
        mock_comments_service.delete_resource_comments.assert_called_once_with(comments)
        mock_comments_service.refresh_resources_comments.assert_called_once_with(
            resource_comment_summaries
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once_with(
            f'{len(comments)} ' + _('bulk delete completed.'),
            allow_html=True,
        )
        mock_url_for.assert_called_once_with(
            'management.comments', tab='resource-comments'
        )
        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.request')
    def test_delete_bulk_resource_comments_without_comment(
        self,
        mock_request,
        mock_url_for,
        mock_redirect,
    ):
        mock_request.form.getlist.return_value = None
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            response = ManagementController.delete_bulk_resource_comments()

        mock_url_for.assert_called_once_with(
            'management.comments', tab='resource-comments'
        )
        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_using_sysadmin(
        self, mock_toolkit_abort
    ):
        mocked_utilization = MagicMock()
        mocked_utilization.resource.package.owner_org = 'owner_org'

        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        ManagementController._check_organization_admin_role_with_utilization(
            [mocked_utilization]
        )
        mock_toolkit_abort.assert_not_called()

    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_using_org_admin(
        self, mock_toolkit_abort
    ):
        mocked_utilization = MagicMock()

        user_dict = factories.User()
        user = User.get(user_dict['id'])
        g.userobj = user

        organization_dict = factories.Organization()
        organization = model.Group.get(organization_dict['id'])

        mocked_utilization.resource.package.owner_org = organization_dict['id']

        member = model.Member(
            group=organization,
            group_id=organization_dict['id'],
            table_id=user.id,
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()

        ManagementController._check_organization_admin_role_with_utilization(
            [mocked_utilization]
        )
        mock_toolkit_abort.assert_not_called()

    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_using_user(
        self, mock_toolkit_abort
    ):
        mocked_utilization = MagicMock()

        user_dict = factories.User()
        user = User.get(user_dict['id'])
        g.userobj = user

        organization_dict = factories.Organization()

        mocked_utilization.resource.package.owner_org = organization_dict['id']

        ManagementController._check_organization_admin_role_with_utilization(
            [mocked_utilization]
        )
        mock_toolkit_abort.assert_called_once_with(
            404,
            _(
                'The requested URL was not found on the server. If you entered the URL'
                ' manually please check your spelling and try again.'
            ),
        )

    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_resource_using_sysadmin(
        self, mock_toolkit_abort
    ):
        mocked_resource_comment_summary = MagicMock()
        mocked_resource_comment_summary.resource.package.owner_org = 'owner_org'

        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        ManagementController._check_organization_admin_role_with_resource(
            [mocked_resource_comment_summary]
        )
        mock_toolkit_abort.assert_not_called()

    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_resource_using_org_admin(
        self, mock_toolkit_abort
    ):
        mocked_resource_comment_summary = MagicMock()

        user_dict = factories.User()
        user = User.get(user_dict['id'])
        g.userobj = user

        organization_dict = factories.Organization()
        organization = model.Group.get(organization_dict['id'])

        mocked_resource_comment_summary.resource.package.owner_org = organization_dict[
            'id'
        ]

        member = model.Member(
            group=organization,
            group_id=organization_dict['id'],
            table_id=user.id,
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()

        ManagementController._check_organization_admin_role_with_resource(
            [mocked_resource_comment_summary]
        )
        mock_toolkit_abort.assert_not_called()

    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_resource_using_user(
        self, mock_toolkit_abort
    ):
        mocked_resource_comment_summary = MagicMock()

        user_dict = factories.User()
        user = User.get(user_dict['id'])
        g.userobj = user

        organization_dict = factories.Organization()

        mocked_resource_comment_summary.resource.package.owner_org = organization_dict[
            'id'
        ]

        ManagementController._check_organization_admin_role_with_resource(
            [mocked_resource_comment_summary]
        )
        mock_toolkit_abort.assert_called_once_with(
            404,
            _(
                'The requested URL was not found on the server. If you entered the URL'
                ' manually please check your spelling and try again.'
            ),
        )
