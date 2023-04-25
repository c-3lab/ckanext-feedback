from unittest.mock import MagicMock, patch

import pytest
import six
from ckan import model
from ckan.logic import get_action
from ckan.model import Resource, Session, User
from ckan.tests import factories
from flask import Flask, g

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.utilization import UtilizationController

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestUtilizationController:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request')
    def test_search(self, mock_request, mock_get_utilizations, mock_render):
        dataset = factories.Dataset()
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        resource = factories.Resource(package_id=dataset['id'])
        user_env = {'REMOTE_USER': user.name}

        keyword = 'keyword'
        disable_keyword = 'disable keyword'

        mock_request.args.get.side_effect = lambda x, default: {
            'id': resource['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(resource['id'], keyword, None)
        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'utilizations': mock_get_utilizations.return_value,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request')
    def test_search_without_user(
        self, mock_request, mock_get_utilizations, mock_render
    ):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        keyword = 'keyword'
        disable_keyword = 'disable keyword'

        mock_request.args.get.side_effect = lambda x, default: {
            'id': resource['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        with self.app.test_request_context(path='/'):
            g.userobj = None
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(resource['id'], keyword, True)
        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'utilizations': mock_get_utilizations.return_value,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.registration_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.request')
    def test_new(self, mock_request, mock_get_resource, mock_render, app):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        mock_request.args.get.side_effect = lambda x, default: {
            'resource_id': resource['id'],
            'return_to_resource': True,
        }.get(x, default)

        resource_object = Resource.get(resource['id'])
        mock_get_resource.return_value = resource_object

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            UtilizationController.new()

        context = {'model': model, 'session': Session, 'for_view': True}
        package = get_action('package_show')(context, {'id': dataset['id']})

        mock_render.assert_called_once_with(
            'utilization/new.html',
            {
                'pkg_dict': package,
                'return_to_resource': True,
                'resource': resource_object,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.request')
    @patch('ckanext.feedback.controllers.utilization.registration_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.redirect')
    def test_create_return_to_resource_true(
        self,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_summary_service,
        mock_registration_service,
        mock_request,
    ):
        package_name = 'package'
        resource_id = 'resource id'
        title = 'title'
        description = 'description'
        return_to_resource = True

        mock_request.form.get.side_effect = [
            package_name,
            resource_id,
            title,
            description,
            return_to_resource,
        ]
        mock_url_for.return_value = 'resource read url'

        UtilizationController.create()

        mock_registration_service.create_utilization.assert_called_with(
            resource_id, title, description
        )
        mock_summary_service.create_utilization_summary.assert_called_with(resource_id)
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with(
            'resource.read', id=package_name, resource_id=resource_id
        )
        mock_redirect.assert_called_with('resource read url')

    @patch('ckanext.feedback.controllers.utilization.request')
    @patch('ckanext.feedback.controllers.utilization.registration_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.redirect')
    def test_create_return_to_resource_false(
        self,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_summary_service,
        mock_registration_service,
        mock_request,
    ):
        package_name = 'package'
        resource_id = 'resource id'
        title = 'title'
        description = 'description'
        return_to_resource = False

        mock_request.form.get.side_effect = [
            package_name,
            resource_id,
            title,
            description,
            return_to_resource,
        ]
        mock_url_for.return_value = 'dataset read url'

        UtilizationController.create()

        mock_registration_service.create_utilization.assert_called_with(
            resource_id, title, description
        )
        mock_summary_service.create_utilization_summary.assert_called_with(resource_id)
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with('dataset.read', id=package_name)
        mock_redirect.assert_called_with('dataset read url')

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request')
    @patch('ckanext.feedback.controllers.utilization.registration_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    def test_create_without_resource_id_title_description(
        self,
        mock_url_for,
        mock_flash_success,
        mock_summary_service,
        mock_registration_service,
        mock_request,
        mock_toolkit_abort,
    ):
        package_name = 'package'
        resource_id = ''
        title = ''
        description = ''
        return_to_resource = True

        mock_request.form.get.side_effect = [
            package_name,
            resource_id,
            title,
            description,
            return_to_resource,
        ]
        mock_url_for.return_value = 'resource read url'

        UtilizationController.create()

        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_details_approval_true(self, mock_render, mock_detail_service):
        utilization_id = 'utilization id'
        g.userobj = None

        mock_detail_service.get_utilization.return_value = 'utilization'
        mock_detail_service.get_utilization_comments.return_value = 'comments'
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        UtilizationController.details(utilization_id)

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comments.assert_called_once_with(
            utilization_id, True
        )
        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_issue_resolutions.assert_called_once_with(
            utilization_id
        )
        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': 'utilization',
                'comments': 'comments',
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_details_approval_false(
        self,
        mock_render,
        mock_detail_service,
    ):
        utilization_id = 'utilization id'
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        g.userobj = user

        mock_detail_service.get_utilization.return_value = 'utilization'
        mock_detail_service.get_utilization_comments.return_value = 'comments'
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        UtilizationController.details(utilization_id)

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_issue_resolutions.assert_called_once_with(
            utilization_id
        )
        mock_detail_service.get_utilization_comments.assert_called_once_with(
            utilization_id, None
        )
        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': 'utilization',
                'comments': 'comments',
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.redirect')
    def test_approve(
        self,
        mock_redirect,
        mock_url_for,
        mock_session_commit,
        mock_summary_service,
        mock_detail_service,
    ):
        utilization_id = 'utilization id'
        resource_id = 'resource id'
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])

        g.userobj = user
        mock_detail_service.get_utilization.return_value = MagicMock(
            resource_id=resource_id
        )
        mock_url_for.return_value = 'utilization details url'

        UtilizationController.approve(utilization_id)

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.approve_utilization.assert_called_once_with(
            utilization_id, user.id
        )
        mock_summary_service.refresh_utilization_summary.assert_called_once_with(
            resource_id
        )
        mock_session_commit.assert_called_once()
        mock_url_for.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with('utilization details url')

    @patch('ckanext.feedback.controllers.utilization.request')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.redirect')
    def test_create_comment(
        self,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_detail_service,
        mock_request,
    ):
        utilization_id = 'utilization id'
        category = 'category'
        content = 'content'

        mock_request.form.get.side_effect = [category, content]
        mock_url_for.return_value = 'utilization details url'

        UtilizationController.create_comment(utilization_id)

        mock_detail_service.create_utilization_comment.assert_called_once_with(
            utilization_id, category, content
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with('utilization details url')

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    def test_create_comment_without_category_content(
        self,
        mock_url_for,
        mock_flash_success,
        mock_detail_service,
        mock_request,
        mock_toolkit_abort,
    ):
        utilization_id = 'utilization id'
        category = ''
        content = ''

        mock_request.form.get.side_effect = [category, content]
        mock_url_for.return_value = 'utilization details url'

        UtilizationController.create_comment(utilization_id)

        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.redirect')
    def test_approve_comment(
        self,
        mock_redirect,
        mock_url_for,
        mock_session_commit,
        mock_detail_service,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])

        mock_url_for.return_value = 'utilization details url'

        g.userobj = user
        UtilizationController.approve_comment(utilization_id, comment_id)

        mock_detail_service.approve_utilization_comment.assert_called_once_with(
            comment_id, user.id
        )
        mock_detail_service.refresh_utilization_comments.assert_called_once_with(
            utilization_id
        )
        mock_session_commit.assert_called_once()
        mock_url_for.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with('utilization details url')

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    def test_edit(
        self,
        mock_edit_service,
        mock_render,
    ):
        utilization_id = 'test utilization id'
        utilization_details = MagicMock()
        resource_details = MagicMock()
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])

        mock_edit_service.get_utilization_details.return_value = utilization_details
        mock_edit_service.get_resource_details.return_value = resource_details

        g.userobj = user
        UtilizationController.edit(utilization_id)

        mock_edit_service.get_utilization_details.assert_called_once_with(
            utilization_id
        )
        mock_edit_service.get_resource_details.assert_called_once_with(
            utilization_details.resource_id
        )
        mock_render.assert_called_once_with(
            'utilization/edit.html',
            {
                'utilization_details': utilization_details,
                'resource_details': resource_details,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.request')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.redirect')
    def test_update(
        self,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_edit_service,
        mock_request,
    ):
        utilization_id = 'utilization id'
        title = 'title'
        description = 'description'

        mock_request.form.get.side_effect = [title, description]
        mock_url_for.return_value = 'utilization details url'

        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.update(utilization_id)

        mock_edit_service.update_utilization.assert_called_once_with(
            utilization_id, title, description
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with('utilization details url')

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    def test_update_without_title_description(
        self,
        mock_url_for,
        mock_flash_success,
        mock_edit_service,
        mock_request,
        mock_toolkit_abort,
    ):
        utilization_id = 'test_utilization_id'
        title = ''
        description = ''

        mock_request.form.get.side_effect = [title, description]
        mock_url_for.return_value = 'utilization_details_url'

        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.update(utilization_id)

        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.redirect')
    @patch('ckanext.feedback.controllers.utilization.c')
    def test_delete(
        self,
        mock_c,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_summary_service,
        mock_edit_service,
        mock_detail_service,
    ):
        utilization_id = 'utilization id'
        resource_id = 'resource id'

        userobj = MagicMock()
        userobj.sysadmin = True
        mock_c.configure_mock(userobj=userobj)

        utilization = MagicMock()
        utilization.resource_id = resource_id
        mock_detail_service.get_utilization.return_value = utilization

        mock_url_for.return_value = 'utilization search url'

        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.delete(utilization_id)

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_edit_service.delete_utilization.assert_called_once_with(utilization_id)
        mock_summary_service.refresh_utilization_summary.assert_called_once_with(
            resource_id
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with('utilization.search')
        mock_redirect.assert_called_once_with('utilization search url')

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_comment(self, mock_render):
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.comment()
        mock_render.assert_called_once_with('utilization/comment.html')

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_comment_approval(self, mock_render):
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.comment_approval()
        mock_render.assert_called_once_with('utilization/comment_approval.html')

    @patch('ckanext.feedback.controllers.utilization.request')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.redirect')
    def test_create_issue_resolution(
        self,
        mock_redirect,
        mock_url_for,
        mock_session_commit,
        mock_summary_service,
        mock_detail_service,
        mock_request,
    ):
        utilization_id = 'utilization id'
        description = 'description'

        mock_request.form.get.return_value = description
        mock_url_for.return_value = 'utilization details url'

        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.create_issue_resolution(utilization_id)

        mock_detail_service.create_issue_resolution.assert_called_once_with(
            utilization_id, description, user.id
        )
        mock_summary_service.increment_issue_resolution_summary.assert_called_once_with(
            utilization_id
        )
        mock_session_commit.assert_called_once()
        mock_url_for.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with('utilization details url')

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    def test_create_issue_resolution_without_description(
        self,
        mock_url_for,
        mock_summary_service,
        mock_detail_service,
        mock_request,
        mock_abort,
    ):
        utilization_id = 'utilization id'
        description = ''

        mock_request.form.get.return_value = description
        mock_url_for.return_value = 'utilization details url'

        with self.app.test_request_context():
            user_dict = factories.Sysadmin()
            user = User.get(user_dict['id'])
            g.userobj = user
            UtilizationController.create_issue_resolution(utilization_id)

        mock_abort.assert_called_once_with(400)
