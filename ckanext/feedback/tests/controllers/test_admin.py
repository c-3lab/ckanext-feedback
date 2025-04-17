import csv
import io
import logging
from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from ckan import model
from ckan.common import _
from ckan.model import User
from ckan.tests import factories
from dateutil.relativedelta import relativedelta
from flask import Flask, Response, g

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.admin import AdminController

log = logging.getLogger(__name__)

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
class TestAdminController:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    def test_admin(
        self,
        mock_render,
        current_user,
        app,
        sysadmin_env,
    ):
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            AdminController.admin()

        mock_render.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.request.args', autospec=True)
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
        active_list = []
        mock_args.get.return_value = 'newest'
        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            url = AdminController.get_href(name, active_list)
        assert (
            '/feedback/admin/approval-and-delete?sort=newest&filter=unapproved' == url
        )

        name = 'unapproved'
        active_list = ['unapproved']
        mock_args.get.return_value = None
        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            url = AdminController.get_href(name, active_list)
        assert '/feedback/admin/approval-and-delete' == url

    @patch('flask_login.utils._get_user')
    @patch(
        'ckanext.feedback.controllers.admin.feedback_service.get_feedbacks_total_count'
    )
    def test_create_filter_dict(
        self,
        mock_get_feedback_total_count,
        current_user,
        app,
        sysadmin_env,
    ):
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        organization = factories.Organization()

        filter_set_name = 'Status'
        name_label_dict = {
            "approved": 'Approved',
            "unapproved": 'Waiting',
        }
        active_filters = []
        org_list = [{'name': organization['name'], 'title': organization['title']}]

        mock_get_feedback_total_count.return_value = {"approved": 0, "unapproved": 1}

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            results = AdminController.create_filter_dict(
                filter_set_name, name_label_dict, active_filters, org_list
            )

        expected_results = {
            'type': 'Status',
            'list': [
                {
                    'name': 'unapproved',
                    'label': 'Waiting',
                    'href': '/feedback/admin/approval-and-delete?filter=unapproved',
                    'count': 1,
                    'active': False,
                }
            ],
        }

        assert results == expected_results

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.request.args')
    @patch('ckanext.feedback.controllers.admin.get_pagination_value')
    @patch('ckanext.feedback.controllers.admin.organization_service')
    @patch('ckanext.feedback.controllers.admin.feedback_service')
    @patch('ckanext.feedback.controllers.admin.AdminController.create_filter_dict')
    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    @patch('ckanext.feedback.controllers.admin.helpers.Page')
    def test_approval_and_delete_with_sysadmin(
        self,
        mock_page,
        mock_render,
        mock_create_filter_dict,
        mock_feedback_service,
        mock_organization_service,
        mock_pagination,
        mock_args,
        current_user,
        app,
        sysadmin_env,
    ):
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=dataset['id'])

        org_list = [
            {'name': organization['name'], 'title': organization['title']},
        ]
        feedback_list = [
            {
                'package_name': dataset['name'],
                'package_title': dataset['title'],
                'resource_id': resource['id'],
                'resource_name': resource['name'],
                'utilization_id': 'util_001',
                'feedback_type': 'リソースコメント',
                'comment_id': 'cmt_001',
                'content': 'リソースコメント テスト001',
                'created': '2025-02-03T12:34:56',
                'is_approved': False,
            },
        ]

        mock_args.getlist.return_value = []
        mock_args.get.return_value = 'newest'
        mock_pagination.return_value = [
            1,
            20,
            0,
            'pager_url',
        ]
        mock_organization_service.get_org_list.return_value = org_list
        mock_feedback_service.get_feedbacks.return_value = feedback_list, len(
            feedback_list
        )
        mock_create_filter_dict.return_value = 'mock_filter'
        mock_page.return_value = 'mock_page'

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            AdminController.approval_and_delete()

        mock_render.assert_called_once_with(
            'admin/approval_and_delete.html',
            {
                "org_list": org_list,
                "filters": ['mock_filter', 'mock_filter', 'mock_filter'],
                "sort": 'newest',
                "page": 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.request.args')
    @patch('ckanext.feedback.controllers.admin.get_pagination_value')
    @patch('ckanext.feedback.controllers.admin.organization_service')
    @patch('ckanext.feedback.controllers.admin.feedback_service')
    @patch('ckanext.feedback.controllers.admin.AdminController.create_filter_dict')
    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    @patch('ckanext.feedback.controllers.admin.helpers.Page')
    def test_approval_and_delete_with_org_admin(
        self,
        mock_page,
        mock_render,
        mock_create_filter_dict,
        mock_feedback_service,
        mock_organization_service,
        mock_pagination,
        mock_args,
        current_user,
        app,
        user_env,
    ):
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        mock_current_user(current_user, user_dict)

        organization_dict = factories.Organization()
        organization = model.Group.get(organization_dict['id'])
        dataset = factories.Dataset(owner_org=organization_dict['id'])
        resource = factories.Resource(package_id=dataset['id'])

        member = model.Member(
            group=organization,
            group_id=organization_dict['id'],
            table_id=user.id,
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()

        org_list = [
            {'name': organization_dict['name'], 'title': organization_dict['title']},
        ]
        feedback_list = [
            {
                'package_name': dataset['name'],
                'package_title': dataset['title'],
                'resource_id': resource['id'],
                'resource_name': resource['name'],
                'utilization_id': 'util_001',
                'feedback_type': 'リソースコメント',
                'comment_id': 'cmt_001',
                'content': 'リソースコメント テスト001',
                'created': '2025-02-03T12:34:56',
                'is_approved': False,
            },
        ]

        mock_args.getlist.return_value = []
        mock_args.get.return_value = 'newest'
        mock_pagination.return_value = [
            1,
            20,
            0,
            'pager_url',
        ]
        mock_organization_service.get_org_list.return_value = org_list
        mock_feedback_service.get_feedbacks.return_value = feedback_list, len(
            feedback_list
        )
        mock_create_filter_dict.return_value = 'mock_filter'
        mock_page.return_value = 'mock_page'

        with app.get(url='/', environ_base=user_env):
            g.userobj = current_user
            AdminController.approval_and_delete()

        mock_render.assert_called_once_with(
            'admin/approval_and_delete.html',
            {
                "org_list": org_list,
                "filters": ['mock_filter', 'mock_filter', 'mock_filter'],
                "sort": 'newest',
                "page": 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.request.args')
    @patch('ckanext.feedback.controllers.admin.get_pagination_value')
    @patch('ckanext.feedback.controllers.admin.organization_service')
    @patch('ckanext.feedback.controllers.admin.feedback_service')
    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    @patch('ckanext.feedback.controllers.admin.helpers.Page')
    def test_approval_and_delete_empty_org_list(
        self,
        mock_page,
        mock_render,
        mock_feedback_service,
        mock_organization_service,
        mock_pagination,
        mock_args,
        current_user,
        app,
        sysadmin_env,
    ):
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        org_list = []
        feedback_list = []

        mock_args.getlist.return_value = []
        mock_args.get.return_value = 'newest'
        mock_pagination.return_value = [
            1,
            20,
            0,
            'pager_url',
        ]
        mock_organization_service.get_org_list.return_value = org_list
        mock_feedback_service.get_feedbacks.return_value = feedback_list, len(
            feedback_list
        )
        mock_page.return_value = 'mock_page'

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            AdminController.approval_and_delete()

        mock_render.assert_called_once_with(
            'admin/approval_and_delete.html',
            {
                "org_list": org_list,
                "filters": [],
                "sort": 'newest',
                "page": 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.request.form.getlist')
    @patch.object(AdminController, 'approve_resource_comments')
    @patch.object(AdminController, 'approve_utilization')
    @patch.object(AdminController, 'approve_utilization_comments')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
    @patch('ckanext.feedback.controllers.admin.toolkit.redirect_to')
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
            AdminController.approve_target()

        mock_approve_resource_comments.assert_called_once_with(resource_comments)
        mock_approve_utilization.assert_called_once_with(utilization)
        mock_approve_utilization_comments.assert_called_once_with(utilization_comments)
        mock_flash_success.assert_called_once_with(
            '3 ' + _('item(s) were approved.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-and-delete')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.request.form.getlist')
    @patch('ckanext.feedback.controllers.admin.AdminController')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
    @patch('ckanext.feedback.controllers.admin.toolkit.redirect_to')
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
            AdminController.approve_target()

        mock_management.approve_resource_comments.assert_not_called()
        mock_management.approve_utilization.assert_not_called()
        mock_management.approve_utilization_comments.assert_not_called()
        mock_flash_success.assert_called_once_with(
            '0 ' + _('item(s) were approved.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-and-delete')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.request.form.getlist')
    @patch.object(AdminController, 'delete_resource_comments')
    @patch.object(AdminController, 'delete_utilization')
    @patch.object(AdminController, 'delete_utilization_comments')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
    @patch('ckanext.feedback.controllers.admin.toolkit.redirect_to')
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
            AdminController.delete_target()

        mock_delete_resource_comments.assert_called_once_with(resource_comments)
        mock_delete_utilization.assert_called_once_with(utilization)
        mock_delete_utilization_comments.assert_called_once_with(utilization_comments)
        mock_flash_success.assert_called_once_with(
            '3 ' + _('item(s) were completely deleted.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-and-delete')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.request.form.getlist')
    @patch('ckanext.feedback.controllers.admin.AdminController')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
    @patch('ckanext.feedback.controllers.admin.toolkit.redirect_to')
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
            AdminController.delete_target()

        mock_management.delete_resource_comments.assert_not_called()
        mock_management.delete_utilization.assert_not_called()
        mock_management.delete_utilization_comments.assert_not_called()
        mock_flash_success.assert_called_once_with(
            '0 ' + _('item(s) were completely deleted.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-and-delete')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.utilization_comments_service')
    @patch('ckanext.feedback.controllers.admin.utilization_service')
    @patch('ckanext.feedback.controllers.admin.session.commit')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
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

        mock_utilization_service.get_utilizations_by_comment_ids.return_value = (
            utilizations
        )

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            AdminController.approve_utilization_comments(target)

        # fmt: off
        # Disable automatic formatting by Black
        mock_utilization_comments_service.get_utilization_comment_ids.\
            assert_called_once_with(target)
        mock_utilization_service.get_utilizations_by_comment_ids.\
            assert_called_once_with(target)
        mock_utilization_comments_service.approve_utilization_comments.\
            assert_called_once_with(target, user_dict['id'])
        mock_utilization_comments_service.refresh_utilizations_comments.\
            assert_called_once_with(utilizations)
        # fmt: on
        mock_session_commit.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.utilization_service')
    @patch('ckanext.feedback.controllers.admin.session.commit')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
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

        mock_utilization_service.get_utilization_details_by_ids.return_value = (
            utilizations
        )

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            AdminController.approve_utilization(target)

        # fmt: off
        # Disable automatic formatting by Black
        mock_utilization_service.get_utilization_ids.\
            assert_called_once_with(target)
        mock_utilization_service.get_utilization_details_by_ids.\
            assert_called_once_with(target)
        mock_utilization_service.approve_utilization.\
            assert_called_once_with(target, user_dict['id'])
        # fmt: on
        mock_session_commit.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.resource_comments_service')
    @patch('ckanext.feedback.controllers.admin.session.commit')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
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
            AdminController.approve_resource_comments(target)

        # fmt: off
        # Disable automatic formatting by Black
        mock_resource_comments_service.get_resource_comment_ids.\
            assert_called_once_with(target)
        mock_resource_comments_service.get_resource_comment_summaries.\
            assert_called_once_with(target)
        mock_resource_comments_service.approve_resource_comments.\
            assert_called_once_with(target, user_dict['id'])
        mock_resource_comments_service.refresh_resources_comments.\
            assert_called_once_with(resource_comment_summaries)
        # fmt: on
        mock_session_commit.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.utilization_comments_service')
    @patch('ckanext.feedback.controllers.admin.utilization_service')
    @patch('ckanext.feedback.controllers.admin.session.commit')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
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

        mock_utilization_service.get_utilizations_by_comment_ids.return_value = (
            utilizations
        )

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            AdminController.delete_utilization_comments(target)

        # fmt: off
        # Disable automatic formatting by Black
        mock_utilization_service.get_utilizations_by_comment_ids.\
            assert_called_once_with(target)
        mock_utilization_comments_service.delete_utilization_comments.\
            assert_called_once_with(target)
        mock_utilization_comments_service.refresh_utilizations_comments.\
            assert_called_once_with(utilizations)
        # fmt: on
        mock_session_commit.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.utilization_service')
    @patch('ckanext.feedback.controllers.admin.session.commit')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
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

        mock_utilization_service.get_utilization_details_by_ids.return_value = (
            utilizations
        )

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            AdminController.delete_utilization(target)

        # fmt: off
        # Disable automatic formatting by Black
        mock_utilization_service.get_utilization_details_by_ids.\
            assert_called_once_with(target)
        mock_utilization_service.delete_utilization.\
            assert_called_once_with(target)
        # fmt: on
        mock_session_commit.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.resource_comments_service')
    @patch('ckanext.feedback.controllers.admin.session.commit')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
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
            AdminController.delete_resource_comments(target)

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
    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_using_sysadmin(
        self, mock_toolkit_abort, current_user
    ):
        mocked_utilization = MagicMock()
        mocked_utilization.resource.package.owner_org = 'owner_org'

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        AdminController._check_organization_admin_role_with_utilization(
            [mocked_utilization]
        )
        mock_toolkit_abort.assert_not_called()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_comment_using_org_admin(
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

        AdminController._check_organization_admin_role_with_utilization_comment(
            [mocked_utilization]
        )
        mock_toolkit_abort.assert_not_called()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_comment_using_user(
        self, mock_toolkit_abort, current_user
    ):
        mocked_utilization = MagicMock()

        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        organization_dict = factories.Organization()

        mocked_utilization.resource.package.owner_org = organization_dict['id']

        AdminController._check_organization_admin_role_with_utilization_comment(
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
    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
    def test_check_organization_admin_role_with_utilization(
        self, mock_toolkit_abort, current_user
    ):
        mocked_utilization = MagicMock()

        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        organization_dict = factories.Organization()

        mocked_utilization.resource.package.owner_org = organization_dict['id']

        AdminController._check_organization_admin_role_with_utilization(
            [mocked_utilization]
        )
        mock_toolkit_abort.assert_called_once_with(
            404,
            _(
                'The requested URL was not found on the server. '
                'If you entered the URL manually please check '
                'your spelling and try again.'
            ),
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
    def test_check_organization_admin_role_with_resource_using_sysadmin(
        self, mock_toolkit_abort, current_user
    ):
        mocked_resource_comment_summary = MagicMock()
        mocked_resource_comment_summary.resource.package.owner_org = 'owner_org'

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        AdminController._check_organization_admin_role_with_resource(
            [mocked_resource_comment_summary]
        )
        mock_toolkit_abort.assert_not_called()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
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

        AdminController._check_organization_admin_role_with_resource(
            [mocked_resource_comment_summary]
        )
        mock_toolkit_abort.assert_not_called()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
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

        AdminController._check_organization_admin_role_with_resource(
            [mocked_resource_comment_summary]
        )
        mock_toolkit_abort.assert_called_once_with(
            404,
            _(
                'The requested URL was not found on the server. If you entered the URL'
                ' manually please check your spelling and try again.'
            ),
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.organization_service')
    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    def test_aggregation_with_sysadmin(
        self,
        mock_render,
        mock_organization_service,
        current_user,
        app,
        sysadmin_env,
    ):
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        organization = factories.Organization()

        today = datetime.now()
        max_month = today.strftime('%Y-%m')
        end_date = today - relativedelta(months=1)
        default_month = end_date.strftime('%Y-%m')
        max_year = today.strftime('%Y')
        year = today - relativedelta(years=1)
        default_year = year.strftime('%Y')

        org_list = [
            {'name': organization['name'], 'title': organization['title']},
        ]

        mock_organization_service.get_org_list.return_value = org_list

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            AdminController.aggregation()

        mock_render.assert_called_once_with(
            'admin/aggregation.html',
            {
                "max_month": max_month,
                "default_month": default_month,
                "max_year": int(max_year),
                "default_year": int(default_year),
                "org_list": org_list,
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.organization_service')
    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    def test_aggregation_with_org_admin(
        self,
        mock_render,
        mock_organization_service,
        current_user,
        app,
        user_env,
    ):
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

        today = datetime.now()
        max_month = today.strftime('%Y-%m')
        end_date = today - relativedelta(months=1)
        default_month = end_date.strftime('%Y-%m')
        max_year = today.strftime('%Y')
        year = today - relativedelta(years=1)
        default_year = year.strftime('%Y')

        org_list = [
            {'name': organization_dict['name'], 'title': organization_dict['title']},
        ]

        mock_organization_service.get_org_list.return_value = org_list

        with app.get(url='/', environ_base=user_env):
            g.userobj = current_user
            AdminController.aggregation()

        mock_render.assert_called_once_with(
            'admin/aggregation.html',
            {
                "max_month": max_month,
                "default_month": default_month,
                "max_year": int(max_year),
                "default_year": int(default_year),
                "org_list": org_list,
            },
        )

    @patch(
        'ckanext.feedback.controllers.admin.aggregation_service.get_resource_details'
    )
    def test_export_csv_response(
        self,
        mock_get_resource_details,
    ):
        mock_get_resource_details.return_value = (
            "Group A",
            "Package B",
            "Resource C",
            "http://example.com",
        )

        MockRow = mock.Mock()
        MockRow.resource_id = "12345"
        MockRow.download = 10
        MockRow.resource_comment = 5
        MockRow.utilization = 20
        MockRow.utilization_comment = 2
        MockRow.issue_resolution = 1
        MockRow.like = 100
        MockRow.rating = 4.5

        results = [MockRow]

        response = AdminController.export_csv_response(results, "test.csv")

        assert response.mimetype == "text/csv charset=utf-8"
        assert (
            "attachment; filename*=UTF-8''test.csv"
            in response.headers["Content-Disposition"]
        )

        output = io.BytesIO(response.data)
        output.seek(0)
        text_wrapper = io.TextIOWrapper(output, encoding='utf-8-sig', newline='')
        reader = csv.reader(text_wrapper)

        header = next(reader)
        expected_header = [
            "resource_id",
            "group_title",
            "package_title",
            "resource_name",
            "download_count",
            "comment_count",
            "utilization_count",
            "utilization_comment_count",
            "issue_resolution_count",
            "like_count",
            "average_rating",
            "url",
        ]
        assert (
            header == expected_header
        ), f"Header mismatch: {header} != {expected_header}"

        row = next(reader)
        expected_row = [
            "12345",
            "Group A",
            "Package B",
            "Resource C",
            "10",
            "5",
            "20",
            "2",
            "1",
            "100",
            "4.5",
            "http://example.com",
        ]
        assert row == expected_row, f"Row mismatch: {row} != {expected_row}"

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.request.args.get')
    @patch('ckanext.feedback.controllers.admin.aggregation_service.get_monthly_data')
    @patch('ckanext.feedback.controllers.admin.AdminController.export_csv_response')
    def test_download_monthly(
        self,
        mock_export,
        mock_get_monthly_data,
        mock_get,
        current_user,
        app,
        sysadmin_env,
    ):
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        mock_get.side_effect = lambda key: {
            "group_added": "Test Organization",
            "month": "2024-03",
        }.get(key)
        mock_get_monthly_data.return_value = ["data1", "data2"]
        mock_export.return_value = Response("mock_csv", mimetype="text/csv")

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            response = AdminController.download_monthly()

        assert response.mimetype == "text/csv", "Mimetype should be 'text/csv'"
        assert response.data == b"mock_csv", "Response content mismatch"

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.request.args.get')
    @patch('ckanext.feedback.controllers.admin.aggregation_service.get_yearly_data')
    @patch('ckanext.feedback.controllers.admin.AdminController.export_csv_response')
    def test_download_yearly(
        self,
        mock_export,
        mock_get_yearly_data,
        mock_get,
        current_user,
        app,
        sysadmin_env,
    ):
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        mock_get.side_effect = lambda key: {
            "group_added": "Test Organization",
            "year": "2024",
        }.get(key)
        mock_get_yearly_data.return_value = ["data1", "data2"]
        mock_export.return_value = Response("mock_csv", mimetype="text/csv")

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            response = AdminController.download_yearly()

        assert response.mimetype == "text/csv", "Mimetype should be 'text/csv'"
        assert response.data == b"mock_csv", "Response content mismatch"

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.admin.request.args.get')
    @patch('ckanext.feedback.controllers.admin.aggregation_service.get_all_time_data')
    @patch('ckanext.feedback.controllers.admin.AdminController.export_csv_response')
    def test_download_all_time(
        self,
        mock_export,
        mock_get_all_time_data,
        mock_get,
        current_user,
        app,
        sysadmin_env,
    ):
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        mock_get.return_value = "Test Organization"
        mock_get_all_time_data.return_value = ["data1", "data2"]
        mock_export.return_value = Response("mock_csv", mimetype="text/csv")

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            response = AdminController.download_all_time()

        assert response.mimetype == "text/csv", "Mimetype should be 'text/csv'"
        assert response.data == b"mock_csv", "Response content mismatch"
