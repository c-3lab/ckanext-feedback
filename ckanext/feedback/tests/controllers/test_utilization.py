from unittest.mock import MagicMock, patch

import pytest
from ckan import model
from ckan.common import _
from ckan.logic import get_action
from ckan.model import Resource, Session, User
from ckan.tests import factories
from flask import Flask, g
from flask_babel import Babel

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.utilization import UtilizationController

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
class TestUtilizationController:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)
        Babel(self.app)

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search(
        self,
        mock_args,
        mock_get_utilizations,
        mock_render,
        current_user,
        app,
        sysadmin_env,
    ):
        dataset = factories.Dataset()
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        resource = factories.Resource(package_id=dataset['id'])

        keyword = 'keyword'
        disable_keyword = 'disable keyword'

        mock_args.get.side_effect = lambda x, default: {
            'id': resource['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource['id'], keyword, None, None, ''
        )
        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'utilizations': mock_get_utilizations.return_value,
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search_with_org_admin(
        self, mock_args, mock_get_utilizations, mock_render, current_user, app, user_env
    ):
        dataset = factories.Dataset()
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        mock_current_user(current_user, user_dict)
        resource = factories.Resource(package_id=dataset['id'])

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

        keyword = 'keyword'
        disable_keyword = 'disable keyword'

        mock_args.get.side_effect = lambda x, default: {
            'id': resource['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        with app.get(url='/', environ_base=user_env):
            g.userobj = current_user
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource['id'], keyword, None, [organization_dict['id']], ''
        )
        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'utilizations': mock_get_utilizations.return_value,
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search_with_user(
        self, mock_args, mock_get_utilizations, mock_render, current_user, app, user_env
    ):
        dataset = factories.Dataset()
        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        resource = factories.Resource(package_id=dataset['id'])

        keyword = 'keyword'
        disable_keyword = 'disable keyword'

        mock_args.get.side_effect = lambda x, default: {
            'id': resource['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        with app.get(url='/', environ_base=user_env):
            g.userobj = current_user
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource['id'], keyword, True, None, ''
        )
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
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search_without_user(
        self, mock_args, mock_get_utilizations, mock_render, app
    ):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        keyword = 'keyword'
        disable_keyword = 'disable keyword'

        mock_args.get.side_effect = lambda x, default: {
            'id': resource['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        with app.get(url='/'):
            g.userobj = None
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource['id'], keyword, True, None, ''
        )
        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'utilizations': mock_get_utilizations.return_value,
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.registration_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_new(
        self, mock_args, mock_get_resource, mock_render, current_user, app, user_env
    ):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        user_dict = factories.User()
        mock_current_user(current_user, user_dict)

        mock_args.get.side_effect = lambda x, default: {
            'resource_id': resource['id'],
            'return_to_resource': True,
        }.get(x, default)

        resource_object = Resource.get(resource['id'])
        mock_get_resource.return_value = resource_object

        with app.get(url='/', environ_base=user_env):
            g.userobj = current_user
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

    @patch('ckanext.feedback.controllers.utilization.request.form')
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
        mock_form,
    ):
        package_name = 'package'
        resource_id = 'resource id'
        title = 'title'
        description = 'description'
        return_to_resource = True

        mock_form.get.side_effect = [
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

    @patch('ckanext.feedback.controllers.utilization.request.form')
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
        mock_form,
    ):
        package_name = 'package'
        resource_id = 'resource id'
        title = 'title'
        description = 'description'
        return_to_resource = False

        mock_form.get.side_effect = [
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
    @patch('ckanext.feedback.controllers.utilization.request.form')
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
        mock_form,
        mock_toolkit_abort,
    ):
        package_name = 'package'
        resource_id = ''
        title = ''
        description = ''
        return_to_resource = True

        mock_form.get.side_effect = [
            package_name,
            resource_id,
            title,
            description,
            return_to_resource,
        ]
        mock_url_for.return_value = 'resource read url'

        UtilizationController.create()

        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.validate_service')
    @patch('ckanext.feedback.controllers.utilization.registration_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.redirect')
    def test_create_with_valid_url(
        self,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_summary_service,
        mock_registration_service,
        mock_validate_service,
        mock_form,
    ):
        package_name = 'package'
        resource_id = 'resource id'
        title = 'title'
        valid_url = 'https://example.com'
        description = 'description'
        return_to_resource = True

        mock_form.get.side_effect = [
            package_name,
            resource_id,
            title,
            valid_url,
            description,
            return_to_resource,
        ]
        mock_url_for.return_value = 'resource read url'
        mock_validate_service.validate_url.return_value = []

        UtilizationController.create()

        mock_validate_service.validate_url.assert_called_once_with(valid_url)
        mock_registration_service.create_utilization.assert_called_with(
            resource_id, title, valid_url, description
        )
        mock_summary_service.create_utilization_summary.assert_called_with(resource_id)
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with(
            'resource.read', id=package_name, resource_id=resource_id
        )
        mock_redirect.assert_called_with('resource read url')

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.UtilizationController.new')
    @patch('ckanext.feedback.controllers.utilization.validate_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    def test_create_with_invalid_url(
        self,
        mock_flash_error,
        mock_validate_service,
        mock_new,
        mock_form,
    ):
        package_name = 'package'
        resource_id = 'resource id'
        title = 'title'
        invalid_url = 'invalid_url'
        description = 'description'
        return_to_resource = True

        mock_form.get.side_effect = [
            package_name,
            resource_id,
            title,
            invalid_url,
            description,
            return_to_resource,
        ]
        mock_validate_service.validate_url.return_value = ['Please provide a valid URL']

        UtilizationController.create()

        mock_flash_error.assert_called_once()
        mock_new.assert_called_once_with(resource_id, title, description)

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_details_approval_with_sysadmin(
        self, mock_render, mock_detail_service, current_user
    ):
        utilization_id = 'utilization id'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        organization_dict = factories.Organization()

        mock_utilization = MagicMock()
        mock_utilization.owner_org = organization_dict['id']
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_detail_service.get_utilization_comments.return_value = 'comments'
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        UtilizationController.details(utilization_id)

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comments.assert_called_once_with(
            utilization_id, None
        )
        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_issue_resolutions.assert_called_once_with(
            utilization_id
        )
        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'comments': 'comments',
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_details_approval_with_org_admin(
        self, mock_render, mock_detail_service, current_user
    ):
        utilization_id = 'utilization id'
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

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

        mock_utilization = MagicMock()
        mock_utilization.owner_org = organization_dict['id']
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_detail_service.get_utilization_comments.return_value = 'comments'
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        UtilizationController.details(utilization_id)

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comments.assert_called_once_with(
            utilization_id, None
        )
        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_issue_resolutions.assert_called_once_with(
            utilization_id
        )
        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'comments': 'comments',
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_details_approval_without_user(self, mock_render, mock_detail_service):
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

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_details_with_user(
        self,
        mock_render,
        mock_detail_service,
        current_user,
    ):
        utilization_id = 'utilization id'
        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        utilization = MagicMock()
        utilization.owner_org = 'organization id'
        mock_detail_service.get_utilization.return_value = utilization
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
            utilization_id, True
        )
        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': utilization,
                'comments': 'comments',
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
            },
        )

    @patch('flask_login.utils._get_user')
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
        current_user,
    ):
        utilization_id = 'utilization id'
        resource_id = 'resource id'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        g.userobj = current_user
        mock_detail_service.get_utilization.return_value = MagicMock(
            resource_id=resource_id
        )
        mock_url_for.return_value = 'utilization details url'

        UtilizationController.approve(utilization_id)

        mock_detail_service.get_utilization.assert_any_call(utilization_id)
        mock_detail_service.approve_utilization.assert_called_once_with(
            utilization_id, user_dict['id']
        )
        mock_summary_service.refresh_utilization_summary.assert_called_once_with(
            resource_id
        )
        mock_session_commit.assert_called_once()
        mock_url_for.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with('utilization details url')

    @patch('ckanext.feedback.controllers.utilization.request.form')
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
        mock_form,
    ):
        utilization_id = 'utilization id'
        category = 'category'
        content = 'content'

        mock_form.get.side_effect = [category, content]
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
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    def test_create_comment_without_category_content(
        self,
        mock_url_for,
        mock_flash_success,
        mock_detail_service,
        mock_form,
        mock_toolkit_abort,
    ):
        utilization_id = 'utilization id'
        category = ''
        content = ''

        mock_form.get.side_effect = [category, content]
        mock_url_for.return_value = 'utilization details url'

        UtilizationController.create_comment(utilization_id)

        mock_toolkit_abort.assert_called_once_with(400)

    @patch('flask_login.utils._get_user')
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
        current_user,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        mock_url_for.return_value = 'utilization details url'

        g.userobj = current_user
        UtilizationController.approve_comment(utilization_id, comment_id)

        mock_detail_service.approve_utilization_comment.assert_called_once_with(
            comment_id, user_dict['id']
        )
        mock_detail_service.refresh_utilization_comments.assert_called_once_with(
            utilization_id
        )
        mock_session_commit.assert_called_once()
        mock_url_for.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with('utilization details url')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_edit(
        self,
        mock_detail_service,
        mock_edit_service,
        mock_render,
        current_user,
    ):
        utilization_id = 'test utilization id'
        utilization_details = MagicMock()
        resource_details = MagicMock()
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        mock_edit_service.get_utilization_details.return_value = utilization_details
        mock_edit_service.get_resource_details.return_value = resource_details

        organization = factories.Organization()
        utilization = MagicMock()
        utilization.owner_org = organization['id']
        mock_detail_service.get_utilization.return_value = utilization

        g.userobj = current_user
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

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.redirect')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_update(
        self,
        mock_detail_service,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_edit_service,
        mock_form,
        current_user,
    ):
        utilization_id = 'utilization id'
        title = 'title'
        description = 'description'

        mock_form.get.side_effect = [title, description]
        mock_url_for.return_value = 'utilization details url'

        organization = factories.Organization()
        utilization = MagicMock()
        utilization.owner_org = organization['id']
        mock_detail_service.get_utilization.return_value = utilization
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
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

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_update_without_title_description(
        self,
        mock_detail_service,
        mock_url_for,
        mock_flash_success,
        mock_edit_service,
        mock_form,
        mock_toolkit_abort,
        current_user,
    ):
        utilization_id = 'test_utilization_id'
        title = ''
        description = ''

        mock_form.get.side_effect = [title, description]
        mock_url_for.return_value = 'utilization_details_url'

        organization = factories.Organization()
        utilization = MagicMock()
        utilization.owner_org = organization['id']
        mock_detail_service.get_utilization.return_value = utilization
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        UtilizationController.update(utilization_id)

        mock_toolkit_abort.assert_called_once_with(400)

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    @patch('ckanext.feedback.controllers.utilization.redirect')
    def test_delete(
        self,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_summary_service,
        mock_edit_service,
        mock_detail_service,
        current_user,
    ):
        utilization_id = 'utilization id'
        resource_id = 'resource id'

        utilization = MagicMock()
        utilization.resource_id = resource_id
        mock_detail_service.get_utilization.return_value = utilization

        mock_url_for.return_value = 'utilization search url'

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        UtilizationController.delete(utilization_id)

        mock_detail_service.get_utilization.assert_any_call(utilization_id)
        mock_edit_service.delete_utilization.asset_called_once_with(utilization_id)
        mock_summary_service.refresh_utilization_summary.assert_called_once_with(
            resource_id
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with('utilization.search')
        mock_redirect.assert_called_once_with('utilization search url')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.request.form')
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
        mock_form,
        current_user,
    ):
        utilization_id = 'utilization id'
        description = 'description'

        mock_form.get.return_value = description
        mock_url_for.return_value = 'utilization details url'

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        UtilizationController.create_issue_resolution(utilization_id)

        mock_detail_service.create_issue_resolution.assert_called_once_with(
            utilization_id, description, user_dict['id']
        )
        mock_summary_service.increment_issue_resolution_summary.assert_called_once_with(
            utilization_id
        )
        mock_session_commit.assert_called_once()
        mock_url_for.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with('utilization details url')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.url_for')
    def test_create_issue_resolution_without_description(
        self,
        mock_url_for,
        mock_summary_service,
        mock_detail_service,
        mock_form,
        mock_abort,
        current_user,
        app,
    ):
        utilization_id = 'utilization id'
        description = ''

        mock_form.get.return_value = description
        mock_url_for.return_value = 'utilization details url'

        with self.app.test_request_context():
            user_dict = factories.Sysadmin()
            mock_current_user(current_user, user_dict)
            g.userobj = current_user
            UtilizationController.create_issue_resolution(utilization_id)

        mock_abort.assert_called_once_with(400)

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_check_organization_adimn_role_with_sysadmin(
        self, mocked_detail_service, mock_toolkit_abort, current_user
    ):
        mocked_utilization = MagicMock()
        mocked_utilization.owner_org = 'organization id'
        mocked_detail_service.get_utilization.return_value = mocked_utilization

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        UtilizationController._check_organization_admin_role('utilization_id')
        mock_toolkit_abort.assert_not_called()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_check_organization_adimn_role_with_org_admin(
        self, mocked_detail_service, mock_toolkit_abort, current_user
    ):
        organization_dict = factories.Organization()
        organization = model.Group.get(organization_dict['id'])

        mocked_utilization = MagicMock()
        mocked_detail_service.get_utilization.return_value = mocked_utilization
        mocked_utilization.owner_org = organization_dict['id']

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        member = model.Member(
            group=organization,
            group_id=organization_dict['id'],
            table_id=user_dict['id'],
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()
        UtilizationController._check_organization_admin_role('utilization_id')
        mock_toolkit_abort.assert_not_called()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_check_organization_adimn_role_with_user(
        self, mocked_detail_service, mock_toolkit_abort, current_user
    ):
        organization_dict = factories.Organization()

        mocked_utilization = MagicMock()
        mocked_detail_service.get_utilization.return_value = mocked_utilization
        mocked_utilization.owner_org = organization_dict['id']
        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        UtilizationController._check_organization_admin_role('utilization_id')
        mock_toolkit_abort.assert_called_once_with(
            404,
            _(
                'The requested URL was not found on the server. If you entered the URL'
                ' manually please check your spelling and try again.'
            ),
        )
