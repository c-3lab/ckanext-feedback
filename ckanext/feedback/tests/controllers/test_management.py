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
    @patch('ckanext.feedback.controllers.management.request.args', autospec=True)
    def test_get_href(
        self,
        mock_args,
        current_user,
        app,
        sysadmin_env,
    ):
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        name = 'unapproved'
        active_list = ['unapproved', 'resource']

        mock_args.get.return_value = None

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            url = ManagementController.get_href(name, active_list)

        assert '/feedback/management/approval-delete?filter=resource' == url

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.request.args')
    @patch('ckanext.feedback.controllers.management.get_pagination_value')
    @patch('ckanext.feedback.controllers.management.feedback_service')
    @patch('ckanext.feedback.controllers.management.organization_service')
    @patch('ckanext.feedback.controllers.management.toolkit.render')
    @patch('ckanext.feedback.controllers.management.helpers.Page')
    def test_admin_with_sysadmin(
        self,
        mock_page,
        mock_render,
        mock_organization_service,
        mock_feedback_service,
        mock_pagination,
        mock_args,
        current_user,
        app,
        sysadmin_env,
    ):
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        organization_dict = factories.Organization()
        dataset_dict = factories.Dataset()
        resource_dict = factories.Dataset()

        active_filters = []
        sort = 'newest'
        limit = 20
        offset = 0
        feedback_list = [
            {
                'package_name': dataset_dict['name'],
                'package_title': dataset_dict['title'],
                'resource_id': resource_dict['id'],
                'resource_name': resource_dict['name'],
                'utilization_id': 'util_001',
                'feedback_type': 'リソースコメント',
                'comment_id': 'cmt_001',
                'content': 'リソースコメント テスト001',
                'created': '2025-02-03T12:34:56',
                'is_approved': False,
            },
        ]
        org_list = [
            {'name': organization_dict['name'], 'title': organization_dict['title']},
        ]

        mock_args.getlist.return_value = active_filters
        mock_args.get.return_value = sort
        mock_pagination.return_value = [
            1,
            limit,
            offset,
            'pager_url',
        ]
        mock_feedback_service.get_feedbacks.return_value = feedback_list, len(
            feedback_list
        )
        mock_organization_service.get_org_list.return_value = org_list
        mock_feedback_service.get_feedbacks_count.return_value = len(feedback_list)
        mock_page.return_value = 'mock_page'

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.admin()

        mock_feedback_service.get_feedbacks.assert_called_once_with(
            active_filters=active_filters, sort=sort, limit=limit, offset=offset
        )
        mock_organization_service.get_org_list.assert_called_once_with()
        mock_render.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.request.args.getlist')
    @patch('ckanext.feedback.controllers.management.request.args.get')
    @patch('ckanext.feedback.controllers.management.get_pagination_value')
    @patch('ckanext.feedback.controllers.management.feedback_service')
    @patch('ckanext.feedback.controllers.management.organization_service')
    @patch('ckanext.feedback.controllers.management.toolkit.render')
    @patch('ckanext.feedback.controllers.management.helpers.Page')
    def test_admin_with_org_admin(
        self,
        mock_page,
        mock_render,
        mock_organization_service,
        mock_feedback_service,
        mock_pagination,
        mock_get,
        mock_getlist,
        current_user,
        app,
        user_env,
    ):
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        mock_current_user(current_user, user_dict)

        organization_dict = factories.Organization()
        organization = model.Group.get(organization_dict['id'])
        dataset_dict = factories.Dataset()
        resource_dict = factories.Dataset()

        member = model.Member(
            group=organization,
            group_id=organization_dict['id'],
            table_id=user.id,
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()

        active_filters = []
        sort = 'newest'
        limit = 20
        offset = 0
        feedback_list = [
            {
                'package_name': dataset_dict['name'],
                'package_title': dataset_dict['title'],
                'resource_id': resource_dict['id'],
                'resource_name': resource_dict['name'],
                'utilization_id': 'util_001',
                'feedback_type': 'リソースコメント',
                'comment_id': 'cmt_001',
                'content': 'リソースコメント テスト001',
                'created': '2025-02-03T12:34:56',
                'is_approved': False,
            },
        ]
        org_list = [
            {'name': organization_dict['name'], 'title': organization_dict['title']},
        ]

        mock_getlist.return_value = active_filters
        mock_get.return_value = sort
        mock_pagination.return_value = [
            1,
            limit,
            offset,
            'pager_url',
        ]
        mock_feedback_service.get_feedbacks.return_value = feedback_list, len(
            feedback_list
        )
        mock_organization_service.get_org_list.return_value = org_list
        mock_feedback_service.get_feedbacks_count.return_value = len(feedback_list)
        mock_page.return_value = 'mock_page'

        with app.get(url='/', environ_base=user_env):
            g.userobj = current_user
            ManagementController.admin()

        mock_feedback_service.get_feedbacks.assert_called_once_with(
            owner_orgs=[organization_dict['id']],
            active_filters=active_filters,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        mock_organization_service.get_org_list.assert_called_once_with(
            [organization_dict['id']]
        )
        mock_render.assert_called_once()
        assert g.pkg_dict['organization']['name'] is not None

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.request.form.getlist')
    @patch.object(ManagementController, 'approve_resource_comments')
    @patch.object(ManagementController, 'approve_utilization')
    @patch.object(ManagementController, 'approve_utilization_comments')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.toolkit.redirect_to')
    def test_approve_target(
        self,
        mock_redirect_to,
        mock_flash_success,
        mock_approve_utilization_comments,
        mock_approve_utilization,
        mock_approve_resource_comments,
        mock_getlist,
        current_user,
        app,
        sysadmin_env,
    ):
        resource_comments = [
            'resource_comment_id',
        ]
        utilization = [
            'utilization_id',
        ]
        utilization_comments = [
            'utilization_comment_id',
        ]

        mock_getlist.side_effect = [
            resource_comments,
            utilization,
            utilization_comments,
        ]
        mock_approve_resource_comments.return_value = 1
        mock_approve_utilization.return_value = 1
        mock_approve_utilization_comments.return_value = 1

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.approve_target()

        mock_approve_resource_comments.assert_called_once_with(resource_comments)
        mock_approve_utilization.assert_called_once_with(utilization)
        mock_approve_utilization_comments.assert_called_once_with(utilization_comments)
        mock_flash_success.assert_called_once_with(
            '3 ' + _('approval completed.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-delete')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.request.form.getlist')
    @patch('ckanext.feedback.controllers.management.ManagementController')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.toolkit.redirect_to')
    def test_approve_target_without_feedbacks(
        self,
        mock_redirect_to,
        mock_flash_success,
        mock_management,
        mock_getlist,
        current_user,
        app,
        sysadmin_env,
    ):
        resource_comments = None
        utilization = None
        utilization_comments = None

        mock_getlist.side_effect = [
            resource_comments,
            utilization,
            utilization_comments,
        ]

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.approve_target()

        mock_management.approve_resource_comments.assert_not_called()
        mock_management.approve_utilization.assert_not_called()
        mock_management.approve_utilization_comments.assert_not_called()
        mock_flash_success.assert_called_once_with(
            '0 ' + _('approval completed.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-delete')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.request.form.getlist')
    @patch.object(ManagementController, 'delete_resource_comments')
    @patch.object(ManagementController, 'delete_utilization')
    @patch.object(ManagementController, 'delete_utilization_comments')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.toolkit.redirect_to')
    def test_delete_target(
        self,
        mock_redirect_to,
        mock_flash_success,
        mock_delete_utilization_comments,
        mock_delete_utilization,
        mock_delete_resource_comments,
        mock_getlist,
        current_user,
        app,
        sysadmin_env,
    ):
        resource_comments = [
            'resource_comment_id',
        ]
        utilization = [
            'utilization_id',
        ]
        utilization_comments = [
            'utilization_comment_id',
        ]

        mock_getlist.side_effect = [
            resource_comments,
            utilization,
            utilization_comments,
        ]
        mock_delete_resource_comments.return_value = 1
        mock_delete_utilization.return_value = 1
        mock_delete_utilization_comments.return_value = 1

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.delete_target()

        mock_delete_resource_comments.assert_called_once_with(resource_comments)
        mock_delete_utilization.assert_called_once_with(utilization)
        mock_delete_utilization_comments.assert_called_once_with(utilization_comments)
        mock_flash_success.assert_called_once_with(
            '3 ' + _('delete completed.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-delete')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.request.form.getlist')
    @patch('ckanext.feedback.controllers.management.ManagementController')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    @patch('ckanext.feedback.controllers.management.toolkit.redirect_to')
    def test_delete_target_without_feedbacks(
        self,
        mock_redirect_to,
        mock_flash_success,
        mock_management,
        mock_getlist,
        current_user,
        app,
        sysadmin_env,
    ):
        resource_comments = None
        utilization = None
        utilization_comments = None

        mock_getlist.side_effect = [
            resource_comments,
            utilization,
            utilization_comments,
        ]

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.delete_target()

        mock_management.delete_resource_comments.assert_not_called()
        mock_management.delete_utilization.assert_not_called()
        mock_management.delete_utilization_comments.assert_not_called()
        mock_flash_success.assert_called_once_with(
            '0 ' + _('delete completed.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-delete')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.utilization_comments_service')
    @patch('ckanext.feedback.controllers.management.utilization_service')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    def test_approve_utilization_comments(
        self,
        mock_flash_success,
        mock_session_commit,
        mock_utilization_service,
        mock_utilization_comments_service,
        current_user,
        app,
        sysadmin_env,
    ):
        target = ['utilization_comment_id']

        mock_utilization_comments_service.get_utilization_comment_ids.return_value = (
            target
        )

        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_utilization_service.get_utilizations.return_value = utilizations

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.approve_utilization_comments(target)

        # fmt: off
        # Disable automatic formatting by Black
        mock_utilization_comments_service.get_utilization_comment_ids.\
            assert_called_once_with(target)
        mock_utilization_service.get_utilizations.assert_called_once_with(target)
        mock_utilization_comments_service.approve_utiliation_comments.\
            assert_called_once_with(target, user_dict['id'])
        mock_utilization_comments_service.refresh_utilizations_comments.\
            assert_called_once_with(utilizations)
        # fmt: on
        mock_session_commit.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.utilization_service')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    def test_approve_utilization(
        self,
        mock_flash_success,
        mock_session_commit,
        mock_utilization_service,
        current_user,
        app,
        sysadmin_env,
    ):
        target = ['utilization_id']

        mock_utilization_service.get_utilization_ids.return_value = target

        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_utilization_service.get_utilizations.return_value = utilizations

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.approve_utilization(target)

        mock_utilization_service.get_utilization_ids.assert_called_once_with(target)
        mock_utilization_service.get_utilizations.assert_called_once_with(target)
        mock_utilization_service.approve_utilization.assert_called_once_with(
            target, user_dict['id']
        )
        mock_session_commit.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.resource_comments_service')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    def test_approve_resource_comments(
        self,
        mock_flash_success,
        mock_session_commit,
        mock_resource_comments_service,
        current_user,
        app,
        sysadmin_env,
    ):
        target = ['resource_comment_id']

        mock_resource_comments_service.get_resource_comment_ids.return_value = target

        resource_comment_summary = MagicMock()
        resource_comment_summary.resource.package.owner_org = 'owner_org'
        resource_comment_summaries = [resource_comment_summary]

        mock_resource_comments_service.get_resource_comment_summaries.return_value = (
            resource_comment_summaries
        )

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.approve_resource_comments(target)

        mock_resource_comments_service.get_resource_comment_ids.assert_called_once_with(
            target
        )
        # fmt: off
        # Disable automatic formatting by Black
        mock_resource_comments_service.get_resource_comment_summaries.\
            assert_called_once_with(target)
        mock_resource_comments_service.approve_resource_comments.\
            assert_called_once_with(target, user_dict['id'])
        mock_resource_comments_service.refresh_resources_comments.\
            assert_called_once_with(resource_comment_summaries)
        # fmt: on
        mock_session_commit.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.utilization_comments_service')
    @patch('ckanext.feedback.controllers.management.utilization_service')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    def test_delete_utilization_comments(
        self,
        mock_flash_success,
        mock_session_commit,
        mock_utilization_service,
        mock_utilization_comments_service,
        current_user,
        app,
        sysadmin_env,
    ):
        target = ['utilization_comment_id']

        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_utilization_service.get_utilizations.return_value = utilizations

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.delete_utilization_comments(target)

        mock_utilization_service.get_utilizations.assert_called_once_with(target)
        # fmt: off
        # Disable automatic formatting by Black
        mock_utilization_comments_service.delete_utilization_comments.\
            assert_called_once_with(target)
        mock_utilization_comments_service.refresh_utilizations_comments.\
            assert_called_once_with(utilizations)
        # fmt: on
        mock_session_commit.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.utilization_service')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    def test_delete_utilization(
        self,
        mock_flash_success,
        mock_session_commit,
        mock_utilization_service,
        current_user,
        app,
        sysadmin_env,
    ):
        target = ['resource_comment_id']

        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_utilization_service.get_utilizations.return_value = utilizations

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.delete_utilization(target)

        mock_utilization_service.get_utilizations.assert_called_once_with(target)
        mock_utilization_service.delete_utilization.assert_called_once_with(target)
        mock_session_commit.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.management.resource_comments_service')
    @patch('ckanext.feedback.controllers.management.session.commit')
    @patch('ckanext.feedback.controllers.management.helpers.flash_success')
    def test_delete_resource_comments(
        self,
        mock_flash_success,
        mock_session_commit,
        mock_resource_comments_service,
        current_user,
        app,
        sysadmin_env,
    ):
        target = ['utilization_id']
        resource_comment_summary = MagicMock()
        resource_comment_summary.resource.package.owner_org = 'owner_org'
        resource_comment_summaries = [resource_comment_summary]

        mock_resource_comments_service.get_resource_comment_summaries.return_value = (
            resource_comment_summaries
        )

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ManagementController.delete_resource_comments(target)

        # fmt: off
        # Disable automatic formatting by Black
        mock_resource_comments_service.get_resource_comment_summaries.\
            assert_called_once_with(target)
        mock_resource_comments_service.delete_resource_comments.\
            assert_called_once_with(target)
        mock_resource_comments_service.refresh_resources_comments.\
            assert_called_once_with(resource_comment_summaries)
        # fmt: on
        mock_session_commit.assert_called_once()

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
