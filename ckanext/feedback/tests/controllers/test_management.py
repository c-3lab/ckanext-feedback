from unittest.mock import MagicMock, patch

import pytest
from ckan import model
from ckan.common import _
from ckan.model import User
from ckan.tests import factories
from flask import Flask, g

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.management import ManagementController

engine = model.repo.session.get_bind()


@pytest.fixture
def sysadmin_env():
    user = factories.SysadminWithToken()
    env = {'Authorization': user['token']}
    return env


@pytest.fixture
def user_env():
    user = factories.UserWithToken()
    env = {'Authorization': user['token']}
    return env


def mock_current_user(current_user, user):
    user_obj = model.User.get(user['name'])
    # mock current_user
    current_user.return_value = user_obj


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

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.toolkit.render')
    @patch('ckanext.feedback.controllers.management.request.args')
    @patch('ckanext.feedback.controllers.management.utilization_detail_service')
    @patch('ckanext.feedback.controllers.management.resource_comment_service')
    def test_comments_with_sysadmin(
        self,
        mock_comment_service,
        mock_detail_service,
        mock_args,
        mock_render,
        current_user,
        app,
        sysadmin_env,
    ):
        categories = ['category']
        utilization_comments = ['utilization_comment']
        resource_comments = ['resource_comment']
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        mock_comment_service.get_resource_comments.return_value = resource_comments
        mock_detail_service.get_utilization_comment_categories.return_value = categories
        mock_detail_service.get_utilization_comments.return_value = utilization_comments
        mock_args.get.return_value = 'utilization-comments'

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.comments()

        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_utilization_comments.assert_called_once()
        mock_comment_service.get_resource_comments.assert_called_once()
        mock_args.get.assert_called_once_with('tab', 'utilization-comments')

        mock_render.assert_called_once_with(
            'management/comments.html',
            {
                'categories': categories,
                'utilization_comments': utilization_comments,
                'resource_comments': resource_comments,
                'tab': 'utilization-comments',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.toolkit.render')
    @patch('ckanext.feedback.controllers.management.request.args')
    @patch('ckanext.feedback.controllers.management.utilization_detail_service')
    @patch('ckanext.feedback.controllers.management.resource_comment_service')
    def test_comments_with_org_admin(
        self,
        mock_comment_service,
        mock_detail_service,
        mock_args,
        mock_render,
        current_user,
        app,
        user_env,
    ):
        categories = ['category']
        utilization_comments = ['utilization_comment']
        resource_comments = ['resource_comment']
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        mock_current_user(current_user, user_dict)

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
        mock_args.get.return_value = 'utilization-comments'

        with app.get(url='/', environ_base=user_env):
            g.userobj = current_user
            ManagementController.comments()

        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_utilization_comments.assert_called_once()
        mock_comment_service.get_resource_comments.assert_called_once()
        mock_args.get.assert_called_once_with('tab', 'utilization-comments')

        mock_render.assert_called_once_with(
            'management/comments.html',
            {
                'categories': categories,
                'utilization_comments': utilization_comments,
                'resource_comments': resource_comments,
                'tab': 'utilization-comments',
            },
        )
        assert g.pkg_dict['organization']['name'] is not None

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management._')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.comments_service')
    @patch('ckanext.feedback.controllers.management.request.form')
    def test_approve_bulk_utilization_comments(
        self,
        mock_form,
        mock_comments_service,
        mock_session_commit,
        mock_flash_success,
        mock_url_for,
        mock_redirect,
        _,
        current_user,
        app,
        sysadmin_env,
    ):
        comments = ['comment']
        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_form.getlist.return_value = comments
        mock_comments_service.get_utilizations.return_value = utilizations
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            response = ManagementController.approve_bulk_utilization_comments()

        mock_form.getlist.assert_called_once_with('utilization-comments-checkbox')
        mock_comments_service.get_utilizations.assert_called_once_with(comments)
        mock_comments_service.approve_utilization_comments.assert_called_once_with(
            comments, user_dict['id']
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

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.request.form')
    def test_approve_bulk_utilization_comments_without_comment(
        self, mock_form, mock_url_for, mock_redirect, current_user, app, sysadmin_env
    ):
        mock_form.getlist.return_value = None
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            response = ManagementController.approve_bulk_utilization_comments()

        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management._')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.comments_service')
    @patch('ckanext.feedback.controllers.management.request.form')
    def test_approve_bulk_resource_comments(
        self,
        mock_form,
        mock_comments_service,
        mock_session_commit,
        mock_flash_success,
        mock_url_for,
        mock_redirect,
        _,
        current_user,
        app,
        sysadmin_env,
    ):
        comments = ['comment']
        resource_comment_summary = MagicMock()
        resource_comment_summary.resource.package.owner_org = 'owner_org'
        resource_comment_summaries = [resource_comment_summary]

        mock_form.getlist.return_value = comments
        mock_comments_service.get_resource_comment_summaries.return_value = (
            resource_comment_summaries
        )
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            response = ManagementController.approve_bulk_resource_comments()

        mock_form.getlist.assert_called_once_with('resource-comments-checkbox')
        mock_comments_service.get_resource_comment_summaries.assert_called_once_with(
            comments
        )
        mock_comments_service.approve_resource_comments.assert_called_once_with(
            comments, user_dict['id']
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

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.request.form')
    def test_approve_bulk_resource_comments_without_comment(
        self,
        mock_form,
        mock_url_for,
        mock_redirect,
        current_user,
        app,
        sysadmin_env,
    ):
        mock_form.getlist.return_value = None
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            response = ManagementController.approve_bulk_resource_comments()

        mock_url_for.assert_called_once_with(
            'management.comments', tab='resource-comments'
        )
        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management._')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.comments_service')
    @patch('ckanext.feedback.controllers.management.request.form')
    def test_delete_bulk_utilization_comments(
        self,
        mock_form,
        mock_comments_service,
        mock_session_commit,
        mock_flash_success,
        mock_url_for,
        mock_redirect,
        _,
        current_user,
        app,
        sysadmin_env,
    ):
        comments = ['comment']
        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_form.getlist.return_value = comments
        mock_comments_service.get_utilizations.return_value = utilizations
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            response = ManagementController.delete_bulk_utilization_comments()

        mock_form.getlist.assert_called_once_with('utilization-comments-checkbox')
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

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.request.form')
    def test_delete_bulk_utilization_comments_without_comment(
        self,
        mock_form,
        mock_url_for,
        mock_redirect,
        current_user,
        app,
        sysadmin_env,
    ):
        mock_form.getlist.return_value = None
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            response = ManagementController.delete_bulk_utilization_comments()

        mock_url_for.assert_called_once_with(
            'management.comments', tab='utilization-comments'
        )
        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management._')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.comments_service')
    @patch('ckanext.feedback.controllers.management.request.form')
    def test_delete_bulk_resource_comments(
        self,
        mock_form,
        mock_comments_service,
        mock_session_commit,
        mock_flash_success,
        mock_url_for,
        mock_redirect,
        _,
        current_user,
        app,
        sysadmin_env,
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

        mock_form.getlist.return_value = comments
        mock_comments_service.get_resource_comment_summaries.return_value = (
            resource_comment_summaries
        )
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            response = ManagementController.delete_bulk_resource_comments()

        mock_form.getlist.assert_called_once_with('resource-comments-checkbox')
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

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.redirect')
    @patch('ckanext.feedback.controllers.management.url_for')
    @patch('ckanext.feedback.controllers.management.request.form')
    def test_delete_bulk_resource_comments_without_comment(
        self,
        mock_form,
        mock_url_for,
        mock_redirect,
        current_user,
        app,
        sysadmin_env,
    ):
        mock_form.getlist.return_value = None
        mock_url_for.return_value = 'url'
        mock_redirect.return_value = 'redirect_response'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            response = ManagementController.delete_bulk_resource_comments()

        mock_url_for.assert_called_once_with(
            'management.comments', tab='resource-comments'
        )
        mock_redirect.assert_called_once_with('url')

        assert response == 'redirect_response'

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_using_sysadmin(
        self, mock_toolkit_abort, current_user
    ):
        mocked_utilization = MagicMock()
        mocked_utilization.resource.package.owner_org = 'owner_org'

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        ManagementController._check_organization_admin_role_with_utilization(
            [mocked_utilization]
        )
        mock_toolkit_abort.assert_not_called()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_using_org_admin(
        self, mock_toolkit_abort, current_user
    ):
        mocked_utilization = MagicMock()

        user_dict = factories.User()
        user = User.get(user_dict['id'])
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

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

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_using_user(
        self, mock_toolkit_abort, current_user
    ):
        mocked_utilization = MagicMock()

        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

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

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_resource_using_sysadmin(
        self, mock_toolkit_abort, current_user
    ):
        mocked_resource_comment_summary = MagicMock()
        mocked_resource_comment_summary.resource.package.owner_org = 'owner_org'

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        ManagementController._check_organization_admin_role_with_resource(
            [mocked_resource_comment_summary]
        )
        mock_toolkit_abort.assert_not_called()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_resource_using_org_admin(
        self, mock_toolkit_abort, current_user
    ):
        mocked_resource_comment_summary = MagicMock()

        user_dict = factories.User()
        user = User.get(user_dict['id'])
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

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

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.toolkit.abort')
    def test_check_organization_admin_role_with_resource_using_user(
        self, mock_toolkit_abort, current_user
    ):
        mocked_resource_comment_summary = MagicMock()

        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

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
