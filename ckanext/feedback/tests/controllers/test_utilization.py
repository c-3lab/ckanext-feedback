from unittest.mock import MagicMock, patch

import pytest
from ckan import model
from ckan.common import _, config
from ckan.logic import get_action
from ckan.model import Session, User
from ckan.tests import factories
from flask import Flask, g
from flask_babel import Babel

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.utilization import UtilizationController
from ckanext.feedback.models.utilization import UtilizationCommentCategory

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
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)
        Babel(self.app)

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search(
        self,
        mock_args,
        mock_get_utilizations,
        mock_get_resource,
        mock_render,
        mock_page,
        mock_pagination,
        current_user,
        app,
        sysadmin_env,
    ):
        dataset = factories.Dataset()
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        resource = factories.Resource(package_id=dataset['id'])

        mock_dataset = MagicMock()
        mock_dataset.owner_org = factories.Organization()['id']
        mock_resource = MagicMock()
        mock_resource.package = mock_dataset
        mock_get_resource.return_value = mock_resource

        keyword = 'keyword'
        disable_keyword = 'disable keyword'

        unapproved_status = 'on'
        approval_status = 'on'

        page = 1
        limit = 20
        offset = 0
        pager_url = 'utilization.search'

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            pager_url,
        ]

        mock_args.get.side_effect = lambda x, default: {
            'id': resource['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource['id'],
            keyword,
            None,
            None,
            '',
            limit,
            offset,
        )

        mock_page.assert_called_once_with(
            collection='mock_utilizations',
            page=page,
            url=pager_url,
            item_count='mock_total_count',
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'approval_status': approval_status,
                'unapproved_status': unapproved_status,
                'page': 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search_with_org_admin(
        self,
        mock_args,
        mock_get_utilizations,
        mock_get_resource,
        mock_render,
        mock_page,
        mock_pagination,
        current_user,
        app,
        user_env,
    ):
        dataset = factories.Dataset()
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        mock_current_user(current_user, user_dict)

        organization_dict = factories.Organization()
        organization = model.Group.get(organization_dict['id'])
        organization.name = 'test organization'

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization_dict['id']
        mock_resource = MagicMock()
        mock_resource.package = mock_dataset
        mock_get_resource.return_value = mock_resource

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

        unapproved_status = 'on'
        approval_status = 'on'

        page = 1
        limit = 20
        offset = 0
        pager_url = 'utilization.search'

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            pager_url,
        ]

        mock_args.get.side_effect = lambda x, default: {
            'id': dataset['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
            'organization': organization.name,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        with app.get(url='/', environ_base=user_env):
            g.userobj = current_user
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            dataset['id'],
            keyword,
            None,
            [organization_dict['id']],
            'test organization',
            limit,
            offset,
        )

        mock_page.assert_called_once_with(
            collection='mock_utilizations',
            page=page,
            url=pager_url,
            item_count='mock_total_count',
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'approval_status': approval_status,
                'unapproved_status': unapproved_status,
                'page': 'mock_page',
            },
        )
        assert g.pkg_dict['organization']['name'] == organization.name

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search_with_user(
        self,
        mock_args,
        mock_get_utilizations,
        mock_get_resource,
        mock_render,
        mock_page,
        mock_pagination,
        current_user,
        app,
        user_env,
    ):
        dataset = factories.Dataset()
        user_dict = factories.User()
        mock_current_user(current_user, user_dict)

        mock_dataset = MagicMock()
        mock_dataset.owner_org = factories.Organization()['id']
        mock_resource = MagicMock()
        mock_resource.package = mock_dataset
        mock_get_resource.return_value = mock_resource

        keyword = 'keyword'
        disable_keyword = 'disable keyword'

        unapproved_status = 'on'
        approval_status = 'on'

        page = 1
        limit = 20
        offset = 0
        pager_url = 'utilization.search'

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            pager_url,
        ]

        mock_args.get.side_effect = lambda x, default: {
            'id': dataset['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        with app.get(url='/', environ_base=user_env):
            g.userobj = current_user
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            dataset['id'],
            keyword,
            True,
            None,
            '',
            limit,
            offset,
        )

        mock_page.assert_called_once_with(
            collection='mock_utilizations',
            page=page,
            url=pager_url,
            item_count='mock_total_count',
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'approval_status': approval_status,
                'unapproved_status': unapproved_status,
                'page': 'mock_page',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search_without_user(
        self,
        mock_args,
        mock_get_utilizations,
        mock_get_resource,
        mock_render,
        mock_page,
        mock_pagination,
        app,
    ):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        mock_dataset = MagicMock()
        mock_dataset.owner_org = factories.Organization()['id']
        mock_resource = MagicMock()
        mock_resource.package = mock_dataset
        mock_resource.organization_name = 'test_organization'
        mock_get_resource.return_value = mock_resource

        keyword = 'keyword'
        disable_keyword = 'disable keyword'

        unapproved_status = 'on'
        approval_status = 'on'

        page = 1
        limit = 20
        offset = 0
        pager_url = 'utilization.search'

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            pager_url,
        ]

        mock_args.get.side_effect = lambda x, default: {
            'id': resource['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        with app.get(url='/'):
            g.userobj = None
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource['id'],
            keyword,
            True,
            None,
            '',
            limit,
            offset,
        )

        mock_page.assert_called_once_with(
            collection='mock_utilizations',
            page=page,
            url=pager_url,
            item_count='mock_total_count',
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'approval_status': approval_status,
                'unapproved_status': unapproved_status,
                'page': 'mock_page',
            },
        )
        assert g.pkg_dict['organization']['name'] == 'test_organization'

    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.model.Group.get')
    @patch('ckanext.feedback.controllers.utilization.model.Package.get')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search_with_package(
        self,
        mock_args,
        mock_get_utilizations,
        mock_get_resource,
        mock_package_get,
        mock_group_get,
        mock_render,
        mock_page,
        mock_pagination,
        app,
    ):
        mock_organization = MagicMock()
        mock_organization.id = 'org_id'
        mock_organization.name = 'org_name'

        mock_dataset = MagicMock()
        mock_dataset.owner_org = mock_organization.id

        mock_get_resource.return_value = None
        mock_package_get.return_value = mock_dataset
        mock_group_get.return_value = mock_organization

        keyword = 'keyword'
        disable_keyword = 'disable keyword'

        unapproved_status = 'on'
        approval_status = 'on'

        page = 1
        limit = 20
        offset = 0
        pager_url = 'utilization.search'

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            pager_url,
        ]

        mock_args.get.side_effect = lambda x, default: {
            'id': mock_dataset.id,
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        with app.get(url='/'):
            g.userobj = None
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            mock_dataset.id,
            keyword,
            True,
            None,
            '',
            limit,
            offset,
        )

        mock_page.assert_called_once_with(
            collection='mock_utilizations',
            page=page,
            url=pager_url,
            item_count='mock_total_count',
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'approval_status': approval_status,
                'unapproved_status': unapproved_status,
                'page': 'mock_page',
            },
        )
        assert g.pkg_dict['organization']['name'] == mock_organization.name

    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.model.Package.get')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search_without_id(
        self,
        mock_args,
        mock_get_utilizations,
        mock_get_resource,
        mock_package_get,
        mock_render,
        mock_page,
        mock_pagination,
        app,
    ):
        mock_get_resource.return_value = None
        mock_package_get.return_value = None

        keyword = 'keyword'
        disable_keyword = 'disable keyword'

        unapproved_status = 'on'
        approval_status = 'on'

        page = 1
        limit = 20
        offset = 0
        pager_url = 'utilization.search'

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            pager_url,
        ]

        mock_args.get.side_effect = lambda x, default: {
            'id': 'test_id',
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        with app.get(url='/'):
            g.userobj = None
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            'test_id',
            keyword,
            True,
            None,
            '',
            limit,
            offset,
        )

        mock_page.assert_called_once_with(
            collection='mock_utilizations',
            page=page,
            url=pager_url,
            item_count='mock_total_count',
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'approval_status': approval_status,
                'unapproved_status': unapproved_status,
                'page': 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
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

        mock_organization = factories.Organization()
        mock_dataset = MagicMock()
        mock_dataset.id = dataset['id']
        mock_dataset.owner_org = mock_organization['id']
        mock_resource = MagicMock()
        mock_resource.Resource.id = resource['id']
        mock_resource.Resource.package = mock_dataset
        mock_resource.organization_id = mock_organization['id']
        mock_resource.organization_name = mock_organization['name']
        mock_get_resource.return_value = mock_resource

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
                'resource': mock_resource.Resource,
            },
        )
        assert g.pkg_dict['organization']['name'] == mock_organization['name']

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_new_with_resource_id(
        self, mock_args, mock_get_resource, mock_render, current_user
    ):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        user_dict = factories.User()
        mock_current_user(current_user, user_dict)

        mock_organization = factories.Organization()
        mock_dataset = MagicMock()
        mock_dataset.id = dataset['id']
        mock_dataset.owner_org = mock_organization['id']
        mock_resource = MagicMock()
        mock_resource.Resource.id = resource['id']
        mock_resource.Resource.package = mock_dataset
        mock_resource.organization_id = mock_organization['id']
        mock_resource.organization_name = mock_organization['name']
        mock_get_resource.return_value = mock_resource

        mock_args.get.side_effect = lambda x, default: {
            'title': 'title',
            'url': '',
            'description': 'description',
        }.get(x, default)

        g.userobj = current_user
        UtilizationController.new(resource_id=resource['id'])

        context = {'model': model, 'session': Session, 'for_view': True}
        package = get_action('package_show')(context, {'id': dataset['id']})

        mock_render.assert_called_once_with(
            'utilization/new.html',
            {
                'pkg_dict': package,
                'return_to_resource': False,
                'resource': mock_resource.Resource,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.registration_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_create_return_to_resource_true(
        self,
        mock_redirect_to,
        mock_flash_success,
        mock_session_commit,
        mock_summary_service,
        mock_registration_service,
        mock_form,
    ):
        package_name = 'package'
        resource_id = 'resource id'
        title = 'title'
        url = 'https://example.com'
        description = 'description'
        return_to_resource = True

        mock_form.get.side_effect = [
            package_name,
            resource_id,
            title,
            url,
            description,
            return_to_resource,
        ]

        UtilizationController.create()

        mock_registration_service.create_utilization.assert_called_with(
            resource_id, title, url, description
        )
        mock_summary_service.create_utilization_summary.assert_called_with(resource_id)
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource.read', id=package_name, resource_id=resource_id
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.registration_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_create_return_to_resource_false(
        self,
        mock_redirect_to,
        mock_flash_success,
        mock_session_commit,
        mock_summary_service,
        mock_registration_service,
        mock_form,
    ):
        package_name = 'package'
        resource_id = 'resource id'
        title = 'title'
        url = ''
        description = 'description'
        return_to_resource = False

        mock_form.get.side_effect = [
            package_name,
            resource_id,
            title,
            url,
            description,
            return_to_resource,
        ]

        UtilizationController.create()

        mock_registration_service.create_utilization.assert_called_with(
            resource_id, title, url, description
        )
        mock_summary_service.create_utilization_summary.assert_called_with(resource_id)
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once_with('dataset.read', id=package_name)

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.registration_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    def test_create_without_resource_id_title_description(
        self,
        mock_flash_success,
        mock_summary_service,
        mock_registration_service,
        mock_form,
        mock_toolkit_abort,
    ):
        package_name = 'package'
        resource_id = ''
        title = ''
        url = ''
        description = ''
        return_to_resource = True

        mock_form.get.side_effect = [
            package_name,
            resource_id,
            title,
            url,
            description,
            return_to_resource,
        ]

        UtilizationController.create()

        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    def test_create_without_bad_recaptcha(
        self,
        mock_flash_error,
        mock_is_recaptcha_verified,
        mock_redirect_to,
        mock_form,
    ):
        package_name = ''
        resource_id = 'resource id'
        title = 'title'
        url = ''
        description = 'description'
        return_to_resource = True

        mock_form.get.side_effect = [
            package_name,
            resource_id,
            title,
            url,
            description,
            return_to_resource,
        ]

        mock_is_recaptcha_verified.return_value = False
        UtilizationController.create()
        mock_redirect_to.assert_called_once_with(
            'utilization.new',
            resource_id=resource_id,
            title=title,
            description=description,
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    def test_create_with_invalid_title_length(
        self,
        mock_flash_error,
        mock_redirect_to,
        mock_form,
    ):
        package_name = 'package'
        resource_id = 'resource id'
        title = (
            'over 50 title'
            'example title'
            'example title'
            'example title'
            'example title'
        )
        valid_url = 'https://example.com'
        description = 'description'
        return_to_resource = True

        mock_form.get.side_effect = lambda x, default: {
            'package_name': package_name,
            'resource_id': resource_id,
            'title': title,
            'url': valid_url,
            'description': description,
            'return_to_resource': return_to_resource,
        }.get(x, default)

        UtilizationController.create()

        mock_flash_error.assert_called_once_with(
            'Please keep the title length below 50',
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with(
            'utilization.new',
            resource_id=resource_id,
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    def test_create_with_invalid_url(
        self,
        mock_flash_error,
        mock_redirect_to,
        mock_form,
    ):
        package_name = 'package'
        resource_id = 'resource id'
        title = 'title'
        invalid_url = 'invalid_url'
        description = 'description'

        mock_form.get.side_effect = lambda x, default: {
            'package_name': package_name,
            'resource_id': resource_id,
            'title': title,
            'url': invalid_url,
            'description': description,
        }.get(x, default)

        UtilizationController.create()

        mock_flash_error.assert_called_once_with(
            'Please provide a valid URL',
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with(
            'utilization.new',
            resource_id=resource_id,
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    def test_create_without_invalid_description_length(
        self,
        mock_flash_error,
        mock_redirect_to,
        mock_form,
    ):
        package_name = 'package'
        resource_id = 'resource id'
        title = 'title'
        valid_url = 'https://example.com'
        description = 'ex'
        while True:
            description += description
            if 2000 < len(description):
                break
        return_to_resource = True

        mock_form.get.side_effect = lambda x, default: {
            'package_name': package_name,
            'resource_id': resource_id,
            'title': title,
            'url': valid_url,
            'description': description,
            'return_to_resource': return_to_resource,
        }.get(x, default)

        UtilizationController.create()

        mock_flash_error.assert_called_once_with(
            'Please keep the description length below 2000',
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with(
            'utilization.new',
            resource_id=resource_id,
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_details_approval_with_sysadmin(
        self,
        mock_render,
        mock_detail_service,
        mock_get_resource,
        mock_page,
        mock_pagination,
        current_user,
    ):
        utilization_id = 'utilization id'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        organization_dict = factories.Organization()

        page = 1
        limit = 20
        offset = 0
        _ = ''

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            _,
        ]

        mock_utilization = MagicMock()
        mock_utilization.owner_org = organization_dict['id']
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_detail_service.get_utilization_comments.return_value = [
            'comments',
            'total_count',
        ]
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization_dict['id']
        mock_resource = MagicMock()
        mock_resource.Resource.package = mock_dataset
        mock_resource.organization_id = organization_dict['id']
        mock_resource.organization_name = organization_dict['name']
        mock_get_resource.return_value = mock_resource

        mock_page.return_value = 'mock_page'

        UtilizationController.details(utilization_id)

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comments.assert_called_once_with(
            utilization_id,
            None,
            limit=limit,
            offset=offset,
        )
        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_issue_resolutions.assert_called_once_with(
            utilization_id
        )

        mock_page.assert_called_once_with(
            collection='comments',
            page=page,
            item_count='total_count',
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
                'selected_category': 'REQUEST',
                'content': '',
                'page': 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_details_approval_with_org_admin(
        self,
        mock_render,
        mock_detail_service,
        mock_get_resource,
        mock_page,
        mock_pagination,
        current_user,
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

        page = 1
        limit = 20
        offset = 0
        _ = ''

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            _,
        ]

        mock_utilization = MagicMock()
        mock_utilization.owner_org = organization_dict['id']
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_detail_service.get_utilization_comments.return_value = [
            'comments',
            'total_count',
        ]
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization_dict['id']
        mock_resource = MagicMock()
        mock_resource.Resource.package = mock_dataset
        mock_resource.organization_id = organization_dict['id']
        mock_resource.organization_name = organization_dict['name']
        mock_get_resource.return_value = mock_resource

        mock_page.return_value = 'mock_page'

        UtilizationController.details(utilization_id)

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comments.assert_called_once_with(
            utilization_id,
            None,
            limit=limit,
            offset=offset,
        )
        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_issue_resolutions.assert_called_once_with(
            utilization_id
        )

        mock_page.assert_called_once_with(
            collection='comments',
            page=page,
            item_count='total_count',
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
                'selected_category': 'REQUEST',
                'content': '',
                'page': 'mock_page',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_details_approval_without_user(
        self,
        mock_render,
        mock_detail_service,
        mock_get_resource,
        mock_page,
        mock_pagination,
    ):
        utilization_id = 'utilization id'
        g.userobj = None

        page = 1
        limit = 20
        offset = 0
        _ = ''

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            _,
        ]

        mock_utilization = MagicMock()
        mock_utilization.resource_id = 'resource id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_detail_service.get_utilization_comments.return_value = [
            'comments',
            'total_count',
        ]
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        mock_dataset = MagicMock()
        mock_dataset.owner_org = factories.Organization()['id']
        mock_resource = MagicMock()
        mock_resource.package = mock_dataset
        mock_get_resource.return_value = mock_resource

        mock_page.return_value = 'mock_page'

        UtilizationController.details(utilization_id)

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comments.assert_called_once_with(
            utilization_id,
            True,
            limit=limit,
            offset=offset,
        )
        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_issue_resolutions.assert_called_once_with(
            utilization_id
        )

        mock_page.assert_called_once_with(
            collection='comments',
            page=page,
            item_count='total_count',
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
                'selected_category': 'REQUEST',
                'content': '',
                'page': 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_details_with_user(
        self,
        mock_render,
        mock_detail_service,
        mock_get_resource,
        mock_page,
        mock_pagination,
        current_user,
    ):
        utilization_id = 'utilization id'
        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        page = 1
        limit = 20
        offset = 0
        _ = ''

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            _,
        ]

        mock_utilization = MagicMock()
        mock_utilization.owner_org = 'organization id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_detail_service.get_utilization_comments.return_value = [
            'comments',
            'total_count',
        ]
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        mock_organization = factories.Organization()
        mock_dataset = MagicMock()
        mock_dataset.owner_org = mock_organization['id']
        mock_resource = MagicMock()
        mock_resource.package = mock_dataset
        mock_resource.organization_name = 'test_organization'
        mock_get_resource.return_value = mock_resource

        mock_page.return_value = 'mock_page'

        UtilizationController.details(utilization_id)

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_issue_resolutions.assert_called_once_with(
            utilization_id
        )
        mock_detail_service.get_utilization_comments.assert_called_once_with(
            utilization_id,
            True,
            limit=limit,
            offset=offset,
        )

        mock_page.assert_called_once_with(
            collection='comments',
            page=page,
            item_count='total_count',
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
                'selected_category': 'REQUEST',
                'content': '',
                'page': 'mock_page',
            },
        )
        assert g.pkg_dict['organization']['name'] == 'test_organization'

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_details_thnak_with_user(
        self,
        mock_render,
        mock_detail_service,
        mock_get_resource,
        mock_page,
        mock_pagination,
        current_user,
    ):
        utilization_id = 'utilization id'
        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        page = 1
        limit = 20
        offset = 0
        _ = ''

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            _,
        ]

        mock_utilization = MagicMock()
        mock_utilization.owner_org = 'organization id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_detail_service.get_utilization_comments.return_value = [
            'comments',
            'total_count',
        ]
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        mock_organization = factories.Organization()
        mock_dataset = MagicMock()
        mock_dataset.owner_org = mock_organization['id']
        mock_resource = MagicMock()
        mock_resource.package = mock_dataset
        mock_resource.organization_name = 'test_organization'
        mock_get_resource.return_value = mock_resource

        mock_page.return_value = 'mock_page'

        UtilizationController.details(utilization_id, category='THANK')

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comment_categories.assert_called_once()
        mock_detail_service.get_issue_resolutions.assert_called_once_with(
            utilization_id
        )
        mock_detail_service.get_utilization_comments.assert_called_once_with(
            utilization_id,
            True,
            limit=limit,
            offset=offset,
        )

        mock_page.assert_called_once_with(
            collection='comments',
            page=page,
            item_count='total_count',
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
                'selected_category': 'THANK',
                'content': '',
                'page': 'mock_page',
            },
        )
        assert g.pkg_dict['organization']['name'] == 'test_organization'

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_approve(
        self,
        mock_redirect_to,
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

        UtilizationController.approve(utilization_id)

        mock_detail_service.get_utilization.assert_any_call(utilization_id)
        mock_detail_service.approve_utilization.assert_called_once_with(
            utilization_id, user_dict['id']
        )
        mock_summary_service.refresh_utilization_summary.assert_called_once_with(
            resource_id
        )
        mock_session_commit.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_create_comment(
        self,
        mock_redirect_to,
        mock_flash_success,
        mock_session_commit,
        mock_detail_service,
        mock_form,
    ):
        utilization_id = 'utilization id'
        category = UtilizationCommentCategory.REQUEST.name
        content = 'content'

        mock_form.get.side_effect = [category, content, True]

        UtilizationController.create_comment(utilization_id)

        mock_detail_service.create_utilization_comment.assert_called_once_with(
            utilization_id, category, content
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    def test_create_comment_without_category_content(
        self,
        mock_flash_success,
        mock_detail_service,
        mock_form,
        mock_toolkit_abort,
    ):
        utilization_id = 'utilization id'
        category = ''
        content = ''

        mock_form.get.side_effect = [category, content, True, True]

        UtilizationController.create_comment(utilization_id)

        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    def test_create_comment_without_comment_length(
        self,
        mock_flash_flash_error,
        mock_redirect_to,
        mock_form,
    ):
        utilization_id = 'utilization id'
        category = UtilizationCommentCategory.REQUEST.name
        content = 'ex'
        while True:
            content += content
            if 1000 < len(content):
                break

        mock_form.get.side_effect = [category, content, True, True]

        UtilizationController.create_comment(utilization_id)

        mock_flash_flash_error.assert_called_once_with(
            'Please keep the comment length below 1000',
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with(
            'utilization.details',
            utilization_id=utilization_id,
            category=category,
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.UtilizationController.details')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    def test_create_comment_without_bad_recaptcha(
        self,
        mock_flash_error,
        mock_is_recaptcha_verified,
        mock_details,
        mock_form,
    ):
        utilization_id = 'utilization_id'
        category = UtilizationCommentCategory.REQUEST.name
        content = 'content'

        mock_form.get.side_effect = [
            category,
            content,
        ]

        mock_is_recaptcha_verified.return_value = False
        UtilizationController.create_comment(utilization_id)
        mock_details.assert_called_once_with(utilization_id, category, content)

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.suggest_ai_comment')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    def test_suggested_comment(
        self,
        mock_get_resource,
        mock_suggest_ai_comment,
        mock_get_utilization,
        mock_render,
    ):
        utilization_id = 'utilization_id'
        category = 'category'
        content = 'comment_content'
        softened = 'mock_softened'

        mock_suggest_ai_comment.return_value = softened

        mock_utilization = MagicMock()
        mock_utilization.resource_id = 'mock_resource_id'
        mock_get_utilization.return_value = mock_utilization

        mock_resource = MagicMock()
        mock_resource.organization_name = 'mock_organization_name'
        mock_get_resource.return_value = mock_resource

        UtilizationController.suggested_comment(utilization_id, category, content)
        mock_render.assert_called_once_with(
            'utilization/suggestion.html',
            {
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'selected_category': category,
                'content': content,
                'softened': softened,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.suggest_ai_comment')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    def test_suggested_comment_is_None(
        self,
        mock_get_resource,
        mock_suggest_ai_comment,
        mock_get_utilization,
        mock_render,
    ):
        utilization_id = 'utilization_id'
        category = 'category'
        content = 'comment_content'
        softened = None

        mock_suggest_ai_comment.return_value = softened

        mock_utilization = MagicMock()
        mock_utilization.resource_id = 'mock_resource_id'
        mock_get_utilization.return_value = mock_utilization

        mock_resource = MagicMock()
        mock_resource.organization_name = 'mock_organization_name'
        mock_get_resource.return_value = mock_resource

        UtilizationController.suggested_comment(utilization_id, category, content)
        mock_render.assert_called_once_with(
            'utilization/expect_suggestion.html',
            {
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'selected_category': category,
                'content': content,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_check_comment_GET(
        self,
        mock_redirect_to,
        mock_form,
    ):
        utilization_id = 'utilization_id'

        mock_form.return_value = 'GET'

        UtilizationController.check_comment(utilization_id)
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_utilization_comment_categories'
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_check_comment_POST_moral_keeper_ai_disable(
        self,
        mock_render,
        mock_get_action,
        mock_get_resource,
        mock_get_utilization,
        mock_get_utilization_comment_categories,
        mock_is_recaptcha_verified,
        mock_form,
        mock_method,
    ):
        utilization_id = 'resource_id'
        category = 'category'
        content = 'comment_content'

        config['ckan.feedback.moral_keeper_ai.enable'] = False

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'comment-suggested': False,
        }.get(x, default)

        mock_utilization = MagicMock()
        mock_utilization.resource_id = 'mock_resource_id'
        mock_get_utilization.return_value = mock_utilization

        mock_resource = MagicMock()
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show

        mock_get_utilization_comment_categories.return_value = 'mock_categories'

        UtilizationController.check_comment(utilization_id)
        mock_render.assert_called_once_with(
            'utilization/comment_check.html',
            {
                'pkg_dict': mock_package,
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'content': content,
                'selected_category': category,
                'categories': 'mock_categories',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_utilization_comment_categories'
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.check_ai_comment')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_check_comment_POST_judgement_True(
        self,
        mock_render,
        mock_get_action,
        mock_check_ai_comment,
        mock_get_resource,
        mock_get_utilization,
        mock_get_utilization_comment_categories,
        mock_is_recaptcha_verified,
        mock_form,
        mock_method,
    ):
        utilization_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        judgement = True

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'comment-suggested': False,
        }.get(x, default)

        mock_check_ai_comment.return_value = judgement

        mock_utilization = MagicMock()
        mock_utilization.resource_id = 'mock_resource_id'
        mock_get_utilization.return_value = mock_utilization

        mock_resource = MagicMock()
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show

        mock_get_utilization_comment_categories.return_value = 'mock_categories'

        UtilizationController.check_comment(utilization_id)
        mock_render.assert_called_once_with(
            'utilization/comment_check.html',
            {
                'pkg_dict': mock_package,
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'content': content,
                'selected_category': category,
                'categories': 'mock_categories',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.check_ai_comment')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'UtilizationController.suggested_comment'
    )
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_utilization_comment_categories'
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_check_comment_POST_judgement_False(
        self,
        mock_get_action,
        mock_get_resource,
        mock_get_utilization,
        mock_get_utilization_comment_categories,
        mock_suggested_comment,
        mock_check_ai_comment,
        mock_is_recaptcha_verified,
        mock_form,
        mock_method,
    ):
        utilization_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        judgement = False

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'comment-suggested': False,
        }.get(x, default)

        mock_check_ai_comment.return_value = judgement

        mock_utilization = MagicMock()
        mock_utilization.resource_id = 'mock_resource_id'
        mock_get_utilization.return_value = mock_utilization

        mock_resource = MagicMock()
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show

        mock_get_utilization_comment_categories.return_value = 'mock_categories'

        UtilizationController.check_comment(utilization_id)
        mock_suggested_comment.assert_called_once_with(
            utilization_id=utilization_id,
            category=category,
            content=content,
        )

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_utilization_comment_categories'
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_check_comment_POST_suggested(
        self,
        mock_render,
        mock_get_action,
        mock_get_resource,
        mock_get_utilization,
        mock_get_utilization_comment_categories,
        mock_is_recaptcha_verified,
        mock_form,
        mock_method,
    ):
        utilization_id = 'resource_id'
        category = 'category'
        content = 'comment_content'

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'comment-suggested': True,
        }.get(x, default)

        mock_utilization = MagicMock()
        mock_utilization.resource_id = 'mock_resource_id'
        mock_get_utilization.return_value = mock_utilization

        mock_resource = MagicMock()
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show

        mock_get_utilization_comment_categories.return_value = 'mock_categories'

        UtilizationController.check_comment(utilization_id)
        mock_render.assert_called_once_with(
            'utilization/comment_check.html',
            {
                'pkg_dict': mock_package,
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'content': content,
                'selected_category': category,
                'categories': 'mock_categories',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_check_comment_POST_no_comment_and_category(
        self,
        mock_redirect_to,
        mock_method,
    ):
        utilization_id = 'utilization_id'
        mock_method.return_value = 'POST'

        mock_MoralKeeperAI = MagicMock()
        mock_MoralKeeperAI.return_value = None

        UtilizationController.check_comment(utilization_id)
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.UtilizationController.details')
    def test_check_comment_POST_bad_recaptcha(
        self,
        mock_details,
        mock_flash_error,
        mock_is_recaptcha_verified,
        mock_form,
        mock_method,
    ):
        utilization_id = 'utilization_id'
        category = 'category'
        content = 'comment_content'

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'comment-suggested': True,
        }.get(x, default)

        mock_is_recaptcha_verified.return_value = False

        UtilizationController.check_comment(utilization_id)
        mock_flash_error.assert_called_once_with(
            'Bad Captcha. Please try again.', allow_html=True
        )
        mock_details.assert_called_once_with(utilization_id, category, content)

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_check_comment_POST_without_validate_comment(
        self,
        mock_redirect_to,
        mock_flash_error,
        mock_is_recaptcha_verified,
        mock_form,
        mock_method,
    ):
        utilization_id = 'utilization_id'
        category = 'category'
        content = 'comment_content'
        while len(content) < 1000:
            content += content

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'comment-suggested': True,
        }.get(x, default)

        mock_is_recaptcha_verified.return_value = True

        UtilizationController.check_comment(utilization_id)
        mock_flash_error.assert_called_once_with(
            'Please keep the comment length below 1000',
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with(
            'utilization.details',
            utilization_id=utilization_id,
            category=category,
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_approve_comment(
        self,
        mock_redirect_to,
        mock_session_commit,
        mock_detail_service,
        current_user,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        g.userobj = current_user
        UtilizationController.approve_comment(utilization_id, comment_id)

        mock_detail_service.approve_utilization_comment.assert_called_once_with(
            comment_id, user_dict['id']
        )
        mock_detail_service.refresh_utilization_comments.assert_called_once_with(
            utilization_id
        )
        mock_session_commit.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_edit(
        self,
        mock_detail_service,
        mock_get_resource,
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

        mock_organization = factories.Organization()
        mock_dataset = MagicMock()
        mock_dataset.owner_org = mock_organization['id']
        mock_resource = MagicMock()
        mock_resource.package = mock_dataset
        mock_resource.organization_name = 'test_organization'
        mock_get_resource.return_value = mock_resource

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
        assert g.pkg_dict['organization']['name'] == 'test_organization'

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_update(
        self,
        mock_detail_service,
        mock_redirect_to,
        mock_flash_success,
        mock_session_commit,
        mock_edit_service,
        mock_form,
        current_user,
    ):
        utilization_id = 'utilization id'
        url = 'https://example.com'
        title = 'title'
        description = 'description'

        mock_form.get.side_effect = [title, url, description]

        organization = factories.Organization()
        utilization = MagicMock()
        utilization.owner_org = organization['id']
        mock_detail_service.get_utilization.return_value = utilization
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        UtilizationController.update(utilization_id)

        mock_edit_service.update_utilization.assert_called_once_with(
            utilization_id, title, url, description
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_update_without_title_description(
        self,
        mock_detail_service,
        mock_flash_success,
        mock_edit_service,
        mock_form,
        mock_toolkit_abort,
        current_user,
    ):
        utilization_id = 'test_utilization_id'
        title = ''
        url = ''
        description = ''

        mock_form.get.side_effect = [title, url, description]

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
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_update_with_invalid_title_length(
        self,
        mock_detail_service,
        mock_flash_error,
        mock_redirect_to,
        mock_form,
        current_user,
    ):
        utilization_id = 'utilization id'
        url = 'https://example.com'
        title = (
            'over 50 title'
            'example title'
            'example title'
            'example title'
            'example title'
        )
        description = 'description'

        mock_form.get.side_effect = [title, url, description]

        organization = factories.Organization()
        utilization = MagicMock()
        utilization.owner_org = organization['id']
        mock_detail_service.get_utilization.return_value = utilization
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        UtilizationController.update(utilization_id)

        mock_flash_error.assert_called_once_with(
            'Please keep the title length below 50',
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with(
            'utilization.edit',
            utilization_id=utilization_id,
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_update_without_url(
        self,
        mock_detail_service,
        mock_flash_error,
        mock_redirect_to,
        mock_form,
        current_user,
    ):
        utilization_id = 'utilization id'
        url = 'test_url'
        title = 'title'
        description = 'description'

        mock_form.get.side_effect = [title, url, description]

        organization = factories.Organization()
        utilization = MagicMock()
        utilization.owner_org = organization['id']
        mock_detail_service.get_utilization.return_value = utilization
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        UtilizationController.update(utilization_id)

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.edit',
            utilization_id=utilization_id,
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_update_with_invalid_description_length(
        self,
        mock_detail_service,
        mock_flash_error,
        mock_redirect_to,
        mock_form,
        current_user,
    ):
        utilization_id = 'utilization id'
        url = 'https://example.com'
        title = 'title'
        description = 'ex'
        while True:
            description += description
            if 2000 < len(description):
                break

        mock_form.get.side_effect = [title, url, description]

        organization = factories.Organization()
        utilization = MagicMock()
        utilization.owner_org = organization['id']
        mock_detail_service.get_utilization.return_value = utilization
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        UtilizationController.update(utilization_id)

        mock_flash_error.assert_called_once_with(
            'Please keep the description length below 2000',
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with(
            'utilization.edit',
            utilization_id=utilization_id,
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_delete(
        self,
        mock_redirect_to,
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

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user
        UtilizationController.delete(utilization_id)

        mock_detail_service.get_utilization.assert_any_call(utilization_id)
        mock_edit_service.delete_utilization.asset_called_once_with(utilization_id)
        mock_summary_service.refresh_utilization_summary.assert_called_once_with(
            resource_id
        )
        assert mock_session_commit.call_count == 2
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once_with('utilization.search')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_create_issue_resolution(
        self,
        mock_redirect_to,
        mock_session_commit,
        mock_summary_service,
        mock_detail_service,
        mock_form,
        current_user,
    ):
        utilization_id = 'utilization id'
        description = 'description'

        mock_form.get.return_value = description

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
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_create_issue_resolution_without_description(
        self,
        mock_redirect_to,
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
        mock_redirect_to.return_value = ''

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
