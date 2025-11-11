import csv
import io
import logging
from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from ckan import model
from dateutil.relativedelta import relativedelta
from flask import Response, g

from ckanext.feedback.controllers.admin import AdminController

log = logging.getLogger(__name__)

engine = model.repo.session.get_bind()


# sysadmin_env and user_env fixtures are not
# needed when using admin_context and user_context
# These fixtures are replaced by the context fixtures from conftest.py


def mock_current_user(current_user, user):
    user_obj = model.User.get(user['name'])
    current_user.return_value = user_obj


def make_mocked_object(owner_org):
    mocked = MagicMock()
    mocked.resource = MagicMock()
    mocked.resource.package = MagicMock()
    mocked.resource.package.owner_org = owner_org
    return mocked


@pytest.mark.db_test
@pytest.mark.usefixtures('admin_context')
@pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
class TestAdminControllerWithContext:

    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    @patch('ckanext.feedback.controllers.admin.toolkit.url_for')
    def test_admin(
        self,
        mock_url_for,
        mock_render,
    ):
        mock_url_for.side_effect = lambda route: f"/{route.replace('.', '/')}"
        AdminController.admin()

        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.admin.request.args', autospec=True)
    @patch('ckanext.feedback.controllers.admin.toolkit.url_for')
    def test_get_href(
        self,
        mock_url_for,
        mock_args,
    ):
        # Mock url_for to return a fixed URL
        mock_url_for.return_value = '/feedback/admin/approval-and-delete'

        name = 'unapproved'
        active_list = []
        mock_args.get.return_value = 'newest'
        url = AdminController.get_href(name, active_list)
        assert (
            '/feedback/admin/approval-and-delete?sort=newest&filter=unapproved' == url
        )

        name = 'unapproved'
        active_list = ['unapproved']
        mock_args.get.return_value = None
        url = AdminController.get_href(name, active_list)
        assert '/feedback/admin/approval-and-delete' == url

    @patch(
        'ckanext.feedback.controllers.admin.feedback_service.get_feedbacks_total_count'
    )
    @patch('ckanext.feedback.controllers.admin.AdminController.get_href')
    def test_create_filter_dict(
        self,
        mock_get_href,
        mock_get_feedback_total_count,
        organization,
    ):
        filter_set_name = 'Status'
        name_label_dict = {
            "approved": 'Approved',
            "unapproved": 'Waiting',
        }
        active_filters = []
        org_list = [{'name': organization['name'], 'title': organization['title']}]

        def _href_side_effect(*args, **kwargs):
            candidate = None

            for a in args:
                if isinstance(a, str) and a in name_label_dict:
                    candidate = a
                    break

            if candidate is None:
                for key in ('name', 'filter', 'filter_name', 'value', 'filter_value'):
                    v = kwargs.get(key)
                    if isinstance(v, str) and v in name_label_dict:
                        candidate = v
                        break

            assert (
                candidate is not None
            ), f"get_href called with unexpected args: args={args}, kwargs={kwargs}"

            return f"/feedback/admin/approval-and-delete?filter={candidate}"

        mock_get_href.side_effect = _href_side_effect

        mock_get_feedback_total_count.return_value = {"approved": 0, "unapproved": 1}

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

        mock_get_feedback_total_count.return_value = {"approved": 1, "unapproved": 0}
        active_filters = ["approved"]

        results = AdminController.create_filter_dict(
            filter_set_name, name_label_dict, active_filters, org_list
        )

        expected_results = {
            'type': 'Status',
            'list': [
                {
                    'name': 'approved',
                    'label': 'Approved',
                    'href': '/feedback/admin/approval-and-delete?filter=approved',
                    'count': 1,
                    'active': True,
                }
            ],
        }

        assert results == expected_results

        mock_get_feedback_total_count.return_value = {"unapproved": 3, "approved": 2}
        active_filters = []

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
                    'count': 3,
                    'active': False,
                },
                {
                    'name': 'approved',
                    'label': 'Approved',
                    'href': '/feedback/admin/approval-and-delete?filter=approved',
                    'count': 2,
                    'active': False,
                },
            ],
        }
        assert results == expected_results

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
        organization,
        dataset,
        resource,
    ):

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
                'feedback_type': 'resource_comment',
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
        organization,
        dataset,
        resource,
        admin_context,
    ):
        user_obj = admin_context.return_value

        organization_model = model.Group.get(organization['id'])

        member = model.Member(
            group=organization_model,
            group_id=organization['id'],
            table_id=user_obj.id,
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()

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
                'feedback_type': 'resource_comment',
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
    ):
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
            [],
            [],
        ]
        mock_approve_resource_comments.return_value = 1
        mock_approve_utilization.return_value = 1
        mock_approve_utilization_comments.return_value = 1

        AdminController.approve_target()

        mock_approve_resource_comments.assert_called_once_with(resource_comments)
        mock_approve_utilization.assert_called_once_with(utilization)
        mock_approve_utilization_comments.assert_called_once_with(utilization_comments)
        mock_flash_success.assert_called_once_with(
            '3 ' + ('item(s) were approved.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-and-delete')

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
    ):
        resource_comments = None
        utilization = None
        utilization_comments = None

        mock_getlist.side_effect = [
            resource_comments,
            utilization,
            utilization_comments,
            [],
            [],
        ]

        AdminController.approve_target()

        mock_management.approve_resource_comments.assert_not_called()
        mock_management.approve_utilization.assert_not_called()
        mock_management.approve_utilization_comments.assert_not_called()
        mock_flash_success.assert_called_once_with(
            '0 ' + ('item(s) were approved.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-and-delete')

    @patch('ckanext.feedback.controllers.admin.helpers.flash_error')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
    @patch('ckanext.feedback.controllers.admin.session.commit')
    @patch(
        'ckanext.feedback.controllers.admin.reply_service.'
        'approve_resource_comment_replies'
    )
    @patch('ckanext.feedback.controllers.admin.request.form.getlist')
    def test_approve_target_replies_success_and_partial(
        self,
        mock_getlist,
        mock_approve_replies,
        mock_session_commit,
        mock_flash_success,
        mock_flash_error,
        admin_context,
    ):
        replies = ['r1', 'r2', 'r3']

        mock_getlist.side_effect = [None, None, None, replies, None]
        mock_approve_replies.return_value = len(replies)

        AdminController.approve_target()

        mock_approve_replies.assert_called_once_with(
            replies, admin_context.return_value.id
        )
        mock_flash_error.assert_not_called()
        mock_flash_success.assert_called()
        mock_approve_replies.reset_mock()
        mock_flash_error.reset_mock()
        mock_flash_success.reset_mock()

        mock_getlist.side_effect = [None, None, None, replies, None]
        mock_approve_replies.return_value = 1

        AdminController.approve_target()

        mock_approve_replies.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('ckanext.feedback.controllers.admin.helpers.flash_error')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
    @patch('ckanext.feedback.controllers.admin.session.commit')
    @patch(
        'ckanext.feedback.services.admin.utilization_comment_replies.'
        'approve_utilization_comment_replies'
    )
    @patch('ckanext.feedback.controllers.admin.request.form.getlist')
    def test_approve_target_util_replies_success_and_partial(
        self,
        mock_getlist,
        mock_approve_util_replies,
        mock_session_commit,
        mock_flash_success,
        mock_flash_error,
        admin_context,
    ):
        util_replies = ['u1', 'u2']
        mock_getlist.side_effect = [None, None, None, None, util_replies]
        mock_approve_util_replies.return_value = len(util_replies)
        AdminController.approve_target()
        mock_flash_error.assert_not_called()
        mock_approve_util_replies.reset_mock()
        mock_flash_error.reset_mock()
        mock_flash_success.reset_mock()
        mock_getlist.side_effect = [None, None, None, None, util_replies]
        mock_approve_util_replies.return_value = 0
        AdminController.approve_target()
        mock_flash_error.assert_called_once()

    # Using admin_context fixture instead of manual flask_login patch
    @patch(
        'ckanext.feedback.controllers.admin.reply_service.'
        'delete_resource_comment_replies'
    )
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
    @patch('ckanext.feedback.controllers.admin.session.commit')
    @patch('ckanext.feedback.controllers.admin.request.form.getlist')
    def test_delete_target_replies_only(
        self,
        mock_getlist,
        mock_session_commit,
        mock_flash_success,
        mock_delete_replies,
        admin_context,
    ):
        # admin_context already provides the sysadmin user
        replies = ['r1', 'r2', 'r3']
        mock_getlist.side_effect = [None, None, None, replies, None]

        AdminController.delete_target()

        mock_delete_replies.assert_called_once_with(replies)
        mock_flash_success.assert_called()

    # Using admin_context fixture instead of manual flask_login patch
    @patch(
        'ckanext.feedback.services.admin.utilization_comment_replies.'
        'delete_utilization_comment_replies'
    )
    @patch('ckanext.feedback.controllers.admin.helpers.flash_success')
    @patch('ckanext.feedback.controllers.admin.session.commit')
    @patch('ckanext.feedback.controllers.admin.request.form.getlist')
    def test_delete_target_util_replies_only(
        self,
        mock_getlist,
        mock_session_commit,
        mock_flash_success,
        mock_delete_util_replies,
        admin_context,
    ):
        # admin_context already provides the sysadmin user
        util_replies = ['u1', 'u2']
        mock_getlist.side_effect = [None, None, None, None, util_replies]

        AdminController.delete_target()

        mock_delete_util_replies.assert_called_once_with(util_replies)
        mock_flash_success.assert_called()

    @pytest.mark.parametrize(
        'sort',
        ['oldest', 'dataset_asc', 'dataset_desc', 'resource_asc', 'resource_desc'],
    )
    @patch('ckanext.feedback.controllers.admin.organization_service')
    @patch('ckanext.feedback.controllers.admin.feedback_service')
    @patch('ckanext.feedback.controllers.admin.get_pagination_value')
    @patch('ckanext.feedback.controllers.admin.request.args')
    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    def test_approval_and_delete_with_filters_and_sorts(
        self,
        mock_render,
        mock_args,
        mock_pagination,
        mock_feedback_service,
        mock_org_service,
        admin_context,
        sort,
    ):
        org_list = [{'name': 'org', 'title': 'Org'}]
        mock_org_service.get_org_list.return_value = org_list
        mock_args.getlist.return_value = ['resource', 'approved']
        mock_args.get.return_value = sort
        mock_pagination.return_value = [1, 20, 0, 'pager_url']
        mock_feedback_service.get_feedbacks.return_value = ([], 0)

        mock_feedback_service.get_feedbacks_total_count.return_value = {
            'approved': 1,
            'unapproved': 1,
            'resource': 1,
            'utilization': 1,
            'util-comment': 1,
            'reply': 1,
            'util-reply': 1,
            'org': 1,
        }
        AdminController.approval_and_delete()
        mock_render.assert_called_once()

        mock_feedback_service.get_feedbacks.assert_called_once()
        _, kwargs = mock_feedback_service.get_feedbacks.call_args
        assert kwargs['active_filters'] == ['resource', 'approved']
        assert kwargs['sort'] == sort

    @patch('ckanext.feedback.controllers.admin.request.args', autospec=True)
    def test_get_href_toggle_multiple_filters(
        self,
        mock_args,
        admin_context,
    ):
        mock_args.get.return_value = 'resource_asc'
        url = AdminController.get_href('resource', ['approved', 'resource'])
        assert url in (
            '/feedback/admin/approval-and-delete?sort=resource_asc&filter=approved',
            '/feedback/admin/approval-and-delete?filter=approved&sort=resource_asc',
        )

    @patch(
        'ckanext.feedback.controllers.admin.feedback_service.get_feedbacks_total_count'
    )
    def test_create_filter_dict_active_and_zero_excluded(
        self, mock_get_counts, admin_context
    ):
        org_list = [{'name': 'o', 'title': 'O'}]
        name_label = {'approved': 'Approved', 'unapproved': 'Waiting'}
        active = ['approved']
        mock_get_counts.return_value = {'approved': 2, 'unapproved': 0}

        result = AdminController.create_filter_dict(
            'Status', name_label, active, org_list
        )

        assert result['type'] == 'Status'
        assert [i['name'] for i in result['list']] == ['approved']
        assert result['list'][0]['active'] is True

    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_comment_sysadmin(
        self, mock_abort, admin_context
    ):
        # admin_context already provides the sysadmin user
        mocked = MagicMock()
        mocked.resource.package.owner_org = 'owner_org'
        AdminController._check_organization_admin_role_with_utilization_comment(
            [mocked]
        )
        mock_abort.assert_not_called()

    @patch(
        'ckanext.feedback.controllers.admin.aggregation_service.get_resource_details'
    )
    def test_export_csv_response_rating_none(self, mock_get_resource_details):
        mock_get_resource_details.return_value = ('G', 'P', 'R', 'http://example.com')
        MockRow = mock.Mock()
        MockRow.resource_id = '1'
        MockRow.download = 0
        MockRow.resource_comment = 0
        MockRow.utilization = 0
        MockRow.utilization_comment = 0
        MockRow.issue_resolution = 0
        MockRow.like = 0
        MockRow.rating = None
        response = AdminController.export_csv_response([MockRow], 't.csv')
        text = io.TextIOWrapper(io.BytesIO(response.data), encoding='utf-8-sig').read()
        assert 'Not rated' in text

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
        admin_context,
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
            [],
            [],
        ]
        mock_delete_resource_comments.return_value = 1
        mock_delete_utilization.return_value = 1
        mock_delete_utilization_comments.return_value = 1

        AdminController.delete_target()

        mock_delete_resource_comments.assert_called_once_with(resource_comments)
        mock_delete_utilization.assert_called_once_with(utilization)
        mock_delete_utilization_comments.assert_called_once_with(utilization_comments)
        mock_flash_success.assert_called_once_with(
            '3 ' + ('item(s) were completely deleted.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-and-delete')

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
    ):
        resource_comments = None
        utilization = None
        utilization_comments = None

        mock_getlist.side_effect = [
            resource_comments,
            utilization,
            utilization_comments,
            [],
            [],
        ]

        AdminController.delete_target()

        mock_management.delete_resource_comments.assert_not_called()
        mock_management.delete_utilization.assert_not_called()
        mock_management.delete_utilization_comments.assert_not_called()
        mock_flash_success.assert_called_once_with(
            '0 ' + ('item(s) were completely deleted.'),
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with('feedback.approval-and-delete')

    @patch('ckanext.feedback.controllers.admin.utilization_comments_service')
    @patch('ckanext.feedback.controllers.admin.utilization_service')
    def test_approve_utilization_comments(
        self,
        mock_utilization_service,
        mock_utilization_comments_service,
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

        AdminController.approve_utilization_comments(target)

        # fmt: off
        # Disable automatic formatting by Black
        mock_utilization_comments_service.get_utilization_comment_ids.\
            assert_called_once_with(target)
        mock_utilization_service.get_utilizations_by_comment_ids.\
            assert_called_once_with(target)
        mock_utilization_comments_service.approve_utilization_comments.\
            assert_called_once_with(target, g.userobj.return_value.id)
        mock_utilization_comments_service.refresh_utilizations_comments.\
            assert_called_once_with(utilizations)
        # fmt: on

    @patch('ckanext.feedback.controllers.admin.utilization_comments_service')
    @patch('ckanext.feedback.controllers.admin.utilization_service')
    @patch('ckanext.feedback.controllers.admin.session')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_error')
    @patch('ckanext.feedback.controllers.admin.log')
    def test_approve_utilization_comments_with_exception(
        self,
        mock_log,
        mock_flash_error,
        mock_session,
        mock_utilization_service,
        mock_utilization_comments_service,
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

        # Simulate exception on commit
        mock_session.commit.side_effect = Exception('Database error')

        result = AdminController.approve_utilization_comments(target)

        assert result == 0
        mock_session.rollback.assert_called_once()
        mock_log.warning.assert_called_once_with(
            'Transaction rolled back for utilization comments approval'
        )
        mock_log.exception.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('ckanext.feedback.controllers.admin.utilization_service')
    def test_approve_utilization(
        self,
        mock_utilization_service,
    ):
        target = ['utilization_id']

        mock_utilization_service.get_utilization_ids.return_value = target

        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_utilization_service.get_utilization_details_by_ids.return_value = (
            utilizations
        )
        mock_utilization_service.get_utilization_resource_ids.return_value = [
            'resource_id'
        ]

        result = AdminController.approve_utilization(target)

        # fmt: off
        # Disable automatic formatting by Black
        mock_utilization_service.get_utilization_ids.\
            assert_called_once_with(target)
        mock_utilization_service.get_utilization_details_by_ids.\
            assert_called_once_with(target)
        mock_utilization_service.get_utilization_resource_ids.\
            assert_called_once_with(target)
        mock_utilization_service.approve_utilization.\
            assert_called_once_with(target, g.userobj.return_value.id)
        mock_utilization_service.refresh_utilization_summary.\
            assert_called_once_with(['resource_id'])
        # fmt: on
        assert result == len(target)

    @patch('ckanext.feedback.controllers.admin.utilization_service')
    @patch('ckanext.feedback.controllers.admin.session')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_error')
    @patch('ckanext.feedback.controllers.admin.log')
    def test_approve_utilization_with_exception(
        self,
        mock_log,
        mock_flash_error,
        mock_session,
        mock_utilization_service,
    ):
        target = ['utilization_id']

        mock_utilization_service.get_utilization_ids.return_value = target

        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_utilization_service.get_utilization_details_by_ids.return_value = (
            utilizations
        )

        # Simulate exception on commit
        mock_session.commit.side_effect = Exception('Database error')

        result = AdminController.approve_utilization(target)

        assert result == 0
        mock_session.rollback.assert_called_once()
        mock_log.warning.assert_called_once_with(
            'Transaction rolled back for utilization approval'
        )
        mock_log.exception.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('ckanext.feedback.controllers.admin.resource_comments_service')
    def test_approve_resource_comments(
        self,
        mock_resource_comments_service,
    ):
        target = ['resource_comment_id']

        mock_resource_comments_service.get_resource_comment_ids.return_value = target

        resource_comment_summary = MagicMock()
        resource_comment_summary.resource.package.owner_org = 'owner_org'
        resource_comment_summaries = [resource_comment_summary]

        mock_resource_comments_service.get_resource_comment_summaries.return_value = (
            resource_comment_summaries
        )

        result = AdminController.approve_resource_comments(target)

        # fmt: off
        # Disable automatic formatting by Black
        mock_resource_comments_service.get_resource_comment_ids.\
            assert_called_once_with(target)
        mock_resource_comments_service.get_resource_comment_summaries.\
            assert_called_once_with(target)
        mock_resource_comments_service.approve_resource_comments.\
            assert_called_once_with(target, g.userobj.return_value.id)
        mock_resource_comments_service.refresh_resources_comments.\
            assert_called_once_with(resource_comment_summaries)
        # fmt: on
        assert result == len(target)

    @patch('ckanext.feedback.controllers.admin.resource_comments_service')
    @patch('ckanext.feedback.controllers.admin.session')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_error')
    @patch('ckanext.feedback.controllers.admin.log')
    def test_approve_resource_comments_with_exception(
        self,
        mock_log,
        mock_flash_error,
        mock_session,
        mock_resource_comments_service,
    ):
        target = ['resource_comment_id']

        mock_resource_comments_service.get_resource_comment_ids.return_value = target

        resource_comment_summary = MagicMock()
        resource_comment_summary.resource.package.owner_org = 'owner_org'
        resource_comment_summaries = [resource_comment_summary]

        mock_resource_comments_service.get_resource_comment_summaries.return_value = (
            resource_comment_summaries
        )

        # Simulate exception on commit
        mock_session.commit.side_effect = Exception('Database error')

        result = AdminController.approve_resource_comments(target)

        assert result == 0
        mock_session.rollback.assert_called_once()
        mock_log.warning.assert_called_once_with(
            'Transaction rolled back for resource comments approval'
        )
        mock_log.exception.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('ckanext.feedback.controllers.admin.utilization_comments_service')
    @patch('ckanext.feedback.controllers.admin.utilization_service')
    def test_delete_utilization_comments(
        self,
        mock_utilization_service,
        mock_utilization_comments_service,
    ):
        target = ['utilization_comment_id']

        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_utilization_service.get_utilizations_by_comment_ids.return_value = (
            utilizations
        )

        AdminController.delete_utilization_comments(target)

        # fmt: off
        mock_utilization_service.\
            get_utilizations_by_comment_ids.assert_called_once_with(
                target
            )
        mock_utilization_comments_service.\
            delete_utilization_comments.assert_called_once_with(
                target
            )
        mock_utilization_comments_service.\
            refresh_utilizations_comments.assert_called_once_with(
                utilizations
            )
        # fmt: on

    @patch('ckanext.feedback.controllers.admin.utilization_comments_service')
    @patch('ckanext.feedback.controllers.admin.utilization_service')
    @patch('ckanext.feedback.controllers.admin.session')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_error')
    @patch('ckanext.feedback.controllers.admin.log')
    def test_delete_utilization_comments_with_exception(
        self,
        mock_log,
        mock_flash_error,
        mock_session,
        mock_utilization_service,
        mock_utilization_comments_service,
    ):
        target = ['utilization_comment_id']

        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_utilization_service.get_utilizations_by_comment_ids.return_value = (
            utilizations
        )

        # Simulate exception on commit
        mock_session.commit.side_effect = Exception('Database error')

        result = AdminController.delete_utilization_comments(target)

        assert result == 0
        mock_session.rollback.assert_called_once()
        mock_log.warning.assert_called_once_with(
            'Transaction rolled back for utilization comments deletion'
        )
        mock_log.exception.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('ckanext.feedback.controllers.admin.utilization_service')
    def test_delete_utilization(
        self,
        mock_utilization_service,
    ):
        target = ['utilization_id']

        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_utilization_service.get_utilization_details_by_ids.return_value = (
            utilizations
        )
        mock_utilization_service.get_utilization_resource_ids.return_value = [
            'resource_id'
        ]

        result = AdminController.delete_utilization(target)

        # fmt: off
        # Disable automatic formatting by Black
        mock_utilization_service.get_utilization_details_by_ids.\
            assert_called_once_with(target)
        mock_utilization_service.get_utilization_resource_ids.\
            assert_called_once_with(target)
        mock_utilization_service.delete_utilization.\
            assert_called_once_with(target)
        mock_utilization_service.refresh_utilization_summary.\
            assert_called_once_with(['resource_id'])
        # fmt: on
        assert result == len(target)

    @patch('ckanext.feedback.controllers.admin.utilization_service')
    @patch('ckanext.feedback.controllers.admin.session')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_error')
    @patch('ckanext.feedback.controllers.admin.log')
    def test_delete_utilization_with_exception(
        self,
        mock_log,
        mock_flash_error,
        mock_session,
        mock_utilization_service,
    ):
        target = ['resource_comment_id']

        utilization = MagicMock()
        utilization.resource.package.owner_org = 'owner_org'
        utilizations = [utilization]

        mock_utilization_service.get_utilization_details_by_ids.return_value = (
            utilizations
        )

        # Simulate exception on commit
        mock_session.commit.side_effect = Exception('Database error')

        result = AdminController.delete_utilization(target)

        assert result == 0
        mock_session.rollback.assert_called_once()
        mock_log.warning.assert_called_once_with(
            'Transaction rolled back for utilization deletion'
        )
        mock_log.exception.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('ckanext.feedback.controllers.admin.resource_comments_service')
    def test_delete_resource_comments(
        self,
        mock_resource_comments_service,
    ):
        target = ['utilization_id']
        resource_comment_summary = MagicMock()
        resource_comment_summary.resource.package.owner_org = 'owner_org'
        resource_comment_summaries = [resource_comment_summary]

        mock_resource_comments_service.get_resource_comment_summaries.return_value = (
            resource_comment_summaries
        )

        result = AdminController.delete_resource_comments(target)

        # fmt: off
        mock_resource_comments_service.\
            get_resource_comment_summaries.assert_called_once_with(
                target
            )
        mock_resource_comments_service.\
            delete_resource_comments.assert_called_once_with(
                target
            )
        mock_resource_comments_service.\
            refresh_resources_comments.assert_called_once_with(
                resource_comment_summaries
            )
        # fmt: on
        assert result == len(target)

    @patch('ckanext.feedback.controllers.admin.resource_comments_service')
    @patch('ckanext.feedback.controllers.admin.session')
    @patch('ckanext.feedback.controllers.admin.helpers.flash_error')
    @patch('ckanext.feedback.controllers.admin.log')
    def test_delete_resource_comments_with_exception(
        self,
        mock_log,
        mock_flash_error,
        mock_session,
        mock_resource_comments_service,
    ):
        target = ['utilization_id']
        resource_comment_summary = MagicMock()
        resource_comment_summary.resource.package.owner_org = 'owner_org'
        resource_comment_summaries = [resource_comment_summary]

        mock_resource_comments_service.get_resource_comment_summaries.return_value = (
            resource_comment_summaries
        )

        # Simulate exception on commit
        mock_session.commit.side_effect = Exception('Database error')

        result = AdminController.delete_resource_comments(target)

        assert result == 0
        mock_session.rollback.assert_called_once()
        mock_log.warning.assert_called_once_with(
            'Transaction rolled back for resource comments deletion'
        )
        mock_log.exception.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
    def test_check_organization_admin_role_with_using_sysadmin(
        self, mock_toolkit_abort
    ):
        mocked_obj = make_mocked_object('owner_org')
        AdminController._check_organization_admin_role_with_resource([mocked_obj])
        mock_toolkit_abort.assert_not_called()

    @patch('ckanext.feedback.controllers.admin.organization_service')
    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    def test_aggregation_with_sysadmin(
        self,
        mock_render,
        mock_organization_service,
        organization,
    ):

        max_month = "2024-01"
        default_month = "2023-12"
        max_year = "2024"
        default_year = "2023"

        org_list = [
            {'name': organization['name'], 'title': organization['title']},
        ]

        mock_organization_service.get_org_list.return_value = org_list

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

    @patch('ckanext.feedback.controllers.admin.request.args.get')
    @patch('ckanext.feedback.controllers.admin.aggregation_service.get_monthly_data')
    @patch('ckanext.feedback.controllers.admin.AdminController.export_csv_response')
    def test_download_monthly(
        self,
        mock_export,
        mock_get_monthly_data,
        mock_get,
    ):
        mock_get.side_effect = lambda key: {
            "group_added": "Test Organization",
            "month": "2024-03",
        }.get(key)
        mock_get_monthly_data.return_value = ["data1", "data2"]
        mock_export.return_value = Response("mock_csv", mimetype="text/csv")

        response = AdminController.download_monthly()

        assert response.mimetype == "text/csv", "Mimetype should be 'text/csv'"
        assert response.data == b"mock_csv", "Response content mismatch"

    @patch('ckanext.feedback.controllers.admin.request.args.get')
    @patch('ckanext.feedback.controllers.admin.aggregation_service.get_yearly_data')
    @patch('ckanext.feedback.controllers.admin.AdminController.export_csv_response')
    def test_download_yearly(
        self,
        mock_export,
        mock_get_yearly_data,
        mock_get,
    ):
        mock_get.side_effect = lambda key: {
            "group_added": "Test Organization",
            "year": "2024",
        }.get(key)
        mock_get_yearly_data.return_value = ["data1", "data2"]
        mock_export.return_value = Response("mock_csv", mimetype="text/csv")

        response = AdminController.download_yearly()

        assert response.mimetype == "text/csv", "Mimetype should be 'text/csv'"
        assert response.data == b"mock_csv", "Response content mismatch"

    @patch('ckanext.feedback.controllers.admin.request.args.get')
    @patch('ckanext.feedback.controllers.admin.aggregation_service.get_all_time_data')
    @patch('ckanext.feedback.controllers.admin.AdminController.export_csv_response')
    def test_download_all_time(
        self,
        mock_export,
        mock_get_all_time_data,
        mock_get,
    ):
        mock_get.return_value = "Test Organization"
        mock_get_all_time_data.return_value = ["data1", "data2"]
        mock_export.return_value = Response("mock_csv", mimetype="text/csv")

        response = AdminController.download_all_time()

        assert response.mimetype == "text/csv", "Mimetype should be 'text/csv'"
        assert response.data == b"mock_csv", "Response content mismatch"


@pytest.mark.db_test
@pytest.mark.usefixtures('user_context')
class TestAdminControllerWithoutContext:
    @patch('ckanext.feedback.controllers.admin.g')
    @patch('ckanext.feedback.services.common.check.is_organization_admin')
    @patch('ckanext.feedback.controllers.admin.current_user', new_callable=MagicMock)
    @patch('ckanext.feedback.controllers.admin.request.args')
    @patch('ckanext.feedback.controllers.admin.get_pagination_value')
    @patch('ckanext.feedback.controllers.admin.organization_service')
    @patch('ckanext.feedback.controllers.admin.feedback_service')
    @patch('ckanext.feedback.controllers.admin.AdminController.create_filter_dict')
    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    @patch('ckanext.feedback.controllers.admin.helpers.Page')
    def test_approval_and_delete_with_organization_admin(
        self,
        mock_page,
        mock_render,
        mock_create_filter_dict,
        mock_feedback_service,
        mock_organization_service,
        mock_pagination,
        mock_args,
        mock_current_user,
        mock_is_organization_admin,
        mock_g,
        organization,
        dataset,
        resource,
    ):
        """Test approval_and_delete with non-sysadmin organization admin user"""
        # Non-sysadmin user who is an organization admin
        mock_is_organization_admin.return_value = True
        mock_current_user.sysadmin = False
        mock_current_user.get_group_ids.return_value = [organization['id']]

        mock_org = MagicMock()
        mock_org.name = organization['name']
        mock_current_user.get_groups.return_value = [mock_org]

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
                'feedback_type': 'resource_comment',
                'comment_id': 'cmt_001',
                'content': 'リソースコメント テスト001',
                'created': '2025-02-03T12:34:56',
                'is_approved': False,
            },
        ]

        mock_args.getlist.return_value = []
        mock_args.get.return_value = 'newest'
        mock_pagination.return_value = [1, 20, 0, 'pager_url']
        mock_organization_service.get_org_list.return_value = org_list
        mock_feedback_service.get_feedbacks.return_value = feedback_list, len(
            feedback_list
        )
        mock_create_filter_dict.return_value = 'mock_filter'
        mock_page.return_value = 'mock_page'

        AdminController.approval_and_delete()

        # Verify method calls in execution order
        mock_current_user.get_group_ids.assert_called_once_with(
            group_type='organization', capacity='admin'
        )
        mock_current_user.get_groups.assert_called_once_with(group_type='organization')

        # Verify g.pkg_dict was set correctly
        assert mock_g.pkg_dict == {
            'organization': {
                'name': organization['name'],
            }
        }

        mock_organization_service.get_org_list.assert_called_once_with(
            [organization['id']]
        )

        mock_feedback_service.get_feedbacks.assert_called_once_with(
            org_list,
            active_filters=[],
            sort='newest',
            limit=20,
            offset=0,
        )

        mock_render.assert_called_once_with(
            'admin/approval_and_delete.html',
            {
                "org_list": org_list,
                "filters": ['mock_filter', 'mock_filter', 'mock_filter'],
                "sort": 'newest',
                "page": 'mock_page',
            },
        )

    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
    def test_check_organization_admin_role_with_using_org_admin(
        self, mock_toolkit_abort, organization, user_context
    ):
        mocked_obj = make_mocked_object('owner_org')

        user_obj = user_context.return_value

        mocked_obj.resource.package.owner_org = organization['id']
        organization_model = model.Group.get(organization['id'])
        member = model.Member(
            group=organization_model,
            group_id=organization['id'],
            table_id=user_obj.id,
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()

        AdminController._check_organization_admin_role_with_resource([mocked_obj])
        mock_toolkit_abort.assert_not_called()

    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
    def test_check_organization_admin_role_with_using_user(
        self, mock_toolkit_abort, organization
    ):
        mocked_obj = MagicMock()

        mocked_obj.resource.package.owner_org = organization['id']

        AdminController._check_organization_admin_role_with_resource([mocked_obj])
        mock_toolkit_abort.assert_called_once_with(
            404,
            (
                'The requested URL was not found on the server. If you entered the URL'
                ' manually please check your spelling and try again.'
            ),
        )

    @patch('ckanext.feedback.controllers.admin.has_organization_admin_role')
    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_comment_without_permission(
        self, mock_toolkit_abort, mock_has_org_admin_role, organization, user_context
    ):
        mock_has_org_admin_role.return_value = False

        mock_utilization = MagicMock()
        mock_utilization.resource.package.owner_org = organization['id']

        AdminController._check_organization_admin_role_with_utilization_comment(
            [mock_utilization]
        )

        mock_has_org_admin_role.assert_called_once_with(organization['id'])
        mock_toolkit_abort.assert_called_once_with(
            404,
            (
                'The requested URL was not found on the server. If you entered'
                ' the URL manually please check your spelling and try again.'
            ),
        )

    @patch('ckanext.feedback.controllers.admin.has_organization_admin_role')
    @patch('ckanext.feedback.controllers.admin.toolkit.abort')
    def test_check_organization_admin_role_with_utilization_without_permission(
        self, mock_toolkit_abort, mock_has_org_admin_role, organization, user_context
    ):
        mock_has_org_admin_role.return_value = False

        mock_utilization = MagicMock()
        mock_utilization.resource.package.owner_org = organization['id']

        AdminController._check_organization_admin_role_with_utilization(
            [mock_utilization]
        )

        mock_has_org_admin_role.assert_called_once_with(organization['id'])
        mock_toolkit_abort.assert_called_once_with(
            404,
            (
                'The requested URL was not found on the server. '
                'If you entered the URL manually please check '
                'your spelling and try again.'
            ),
        )

    @patch('ckanext.feedback.controllers.admin.organization_service')
    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    def test_aggregation_with_org_admin(
        self,
        mock_render,
        mock_organization_service,
        organization,
        user_context,
    ):
        user_obj = user_context.return_value

        organization_model = model.Group.get(organization['id'])

        member = model.Member(
            group=organization_model,
            group_id=organization['id'],
            table_id=user_obj.id,
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
            {'name': organization['name'], 'title': organization['title']},
        ]

        mock_organization_service.get_org_list.return_value = org_list

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

    @patch('ckanext.feedback.controllers.admin.request.args')
    @patch('ckanext.feedback.controllers.admin.get_pagination_value')
    @patch('ckanext.feedback.controllers.admin.organization_service')
    @patch('ckanext.feedback.controllers.admin.feedback_service')
    @patch('ckanext.feedback.controllers.admin.toolkit.render')
    @patch('ckanext.feedback.controllers.admin.helpers.Page')
    @patch('ckanext.feedback.controllers.admin.log.debug')
    def test_approval_and_delete_log_debug_exception(
        self,
        mock_log_debug,
        mock_page,
        mock_render,
        mock_feedback_service,
        mock_organization_service,
        mock_pagination,
        mock_args,
        admin_context,
    ):
        mock_log_debug.side_effect = Exception('boom')
        mock_args.getlist.return_value = []
        mock_args.get.return_value = 'newest'
        mock_pagination.return_value = [1, 20, 0, 'pager_url']
        mock_organization_service.get_org_list.return_value = []
        mock_feedback_service.get_feedbacks.return_value = ([], 0)
        mock_page.return_value = 'page'
        mock_render.return_value = 'rendered'

        AdminController.approval_and_delete()
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.admin.utilization_comments_service')
    @patch('ckanext.feedback.controllers.admin.utilization_service')
    def test_approve_utilization_comments_executes(
        self,
        mock_utilization_service,
        mock_utilization_comments_service,
        admin_context,
    ):
        target = ['uc1']
        mock_utilization_comments_service.get_utilization_comment_ids.return_value = (
            target
        )
        util = MagicMock()
        util.resource.package.owner_org = 'org1'
        mock_utilization_service.get_utilizations_by_comment_ids.return_value = [util]

        ret = AdminController.approve_utilization_comments(target)

        assert ret == 1
        # fmt: off
        mock_utilization_comments_service.\
            approve_utilization_comments.assert_called_once(

            )
        mock_utilization_comments_service.\
            refresh_utilizations_comments.assert_called_once(

            )
        # fmt: on

    @patch('ckanext.feedback.controllers.admin.resource_comments_service')
    def test_approve_resource_comments_executes(
        self,
        mock_resource_comments_service,
        admin_context,
    ):
        target = ['rc1']
        mock_resource_comments_service.get_resource_comment_ids.return_value = target
        summary = MagicMock()
        summary.resource.package.owner_org = 'org1'
        mock_resource_comments_service.get_resource_comment_summaries.return_value = [
            summary
        ]

        ret = AdminController.approve_resource_comments(target)

        assert ret == 1
        mock_resource_comments_service.approve_resource_comments.assert_called_once()
        mock_resource_comments_service.refresh_resources_comments.assert_called_once()

    @patch('ckanext.feedback.controllers.admin.utilization_comments_service')
    @patch('ckanext.feedback.controllers.admin.utilization_service')
    def test_delete_utilization_comments_executes(
        self,
        mock_utilization_service,
        mock_utilization_comments_service,
        admin_context,
    ):
        target = ['uc1']
        util = MagicMock()
        util.resource.package.owner_org = 'org1'
        # fmt: off
        mock_utilization_service.\
            get_utilizations_by_comment_ids.return_value = [util]
        ret = AdminController.delete_utilization_comments(target)

        assert ret == 1
        mock_utilization_comments_service.\
            delete_utilization_comments.assert_called_once(

            )
        mock_utilization_comments_service.\
            refresh_utilizations_comments.assert_called_once(

            )
        # fmt:on

    @patch('ckanext.feedback.controllers.admin.utilization_service')
    def test_delete_utilization_executes(
        self,
        mock_utilization_service,
        admin_context,
    ):
        target = ['u1']
        util = MagicMock()
        util.owner_org = 'org1'
        mock_utilization_service.get_utilization_details_by_ids.return_value = [util]
        mock_utilization_service.get_utilization_resource_ids.return_value = ['r1']

        ret = AdminController.delete_utilization(target)

        assert ret == 1
        mock_utilization_service.delete_utilization.assert_called_once()
        mock_utilization_service.refresh_utilization_summary.assert_called_once_with(
            ['r1']
        )

    @patch('ckanext.feedback.controllers.admin.resource_comments_service')
    def test_delete_resource_comments_executes(
        self,
        mock_resource_comments_service,
        admin_context,
    ):
        target = ['rc1']
        summary = MagicMock()
        summary.resource.package.owner_org = 'org1'
        mock_resource_comments_service.get_resource_comment_summaries.return_value = [
            summary
        ]

        ret = AdminController.delete_resource_comments(target)

        assert ret == 1
        mock_resource_comments_service.delete_resource_comments.assert_called_once_with(
            target
        )
        mock_resource_comments_service.refresh_resources_comments.assert_called_once()
