from unittest.mock import MagicMock, patch

import pytest
from ckan import model
from ckan.common import _, config
from ckan.plugins import toolkit
from ckan.tests import factories
from werkzeug.exceptions import NotFound

from ckanext.feedback.controllers.utilization import UtilizationController
from ckanext.feedback.models.types import MoralCheckAction
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


@pytest.mark.db_test
@pytest.mark.usefixtures("admin_context")
class TestUtilizationController:

    @patch('ckanext.feedback.controllers.utilization.get_action')
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
        mock_get_action,
        resource,
        organization,
        admin_context,
        mock_resource_object,
    ):

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization['id']
        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show

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

        UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource['id'],
            keyword,
            None,
            None,
            '',
            limit,
            offset,
            'all',
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

    @patch('ckanext.feedback.controllers.utilization.get_action')
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
        mock_get_action,
        organization,
        dataset,
        user,
        mock_resource_object,
        user_context,
    ):

        organization_model = model.Group.get(organization['id'])
        organization_model.name = 'test organization'

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization['id']
        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show

        member = model.Member(
            group=organization_model,
            group_id=organization['id'],
            table_id=user['id'],
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
            'organization': organization_model.name,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            dataset['id'],
            keyword,
            None,
            [organization['id']],
            'test organization',
            limit,
            offset,
            [organization['id']],
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
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.get_action')
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
        mock_get_action,
        dataset,
        user,
        organization,
        mock_resource_object,
        user_context,
    ):

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization['id']
        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show

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

        UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            dataset['id'],
            keyword,
            True,
            None,
            '',
            limit,
            offset,
            [],
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

    @patch('ckanext.feedback.controllers.utilization.get_action')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    @patch('ckanext.feedback.controllers.utilization.current_user')
    def test_search_without_user(
        self,
        mock_current_user_fixture,
        mock_args,
        mock_get_utilizations,
        mock_get_resource,
        mock_render,
        mock_page,
        mock_pagination,
        mock_get_action,
        app,
        resource,
        organization,
        mock_resource_object,
    ):

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization['id']
        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='test_organization'
        )
        mock_get_resource.return_value = mock_resource
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
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

        UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource['id'],
            keyword,
            True,
            None,
            '',
            limit,
            offset,
            None,
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
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.get_action')
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
        mock_get_action,
        app,
    ):
        mock_organization = MagicMock()
        mock_organization.id = 'org_id'
        mock_organization.name = 'org_name'

        mock_dataset = MagicMock()
        mock_dataset.id = 'package_id'
        mock_dataset.owner_org = mock_organization.id

        mock_get_resource.return_value = None
        mock_package_get.return_value = mock_dataset
        mock_group_get.return_value = mock_organization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show

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

        UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            mock_dataset.id,
            keyword,
            None,
            None,
            '',
            limit,
            offset,
            'all',
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
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.get_action')
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
        mock_get_action,
    ):
        mock_get_resource.return_value = None
        mock_package_get.return_value = None
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show

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

        UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            'test_id',
            keyword,
            None,
            None,
            '',
            limit,
            offset,
            'all',
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

    @patch(
        'ckanext.feedback.controllers.utilization.current_user',
        new_callable=lambda: str,
    )
    @patch('ckanext.feedback.controllers.utilization.get_action')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search_with_private_package_unauthorized(
        self,
        mock_args,
        mock_get_resource,
        mock_get_action,
        mock_current_user_fixture,
        resource,
        mock_resource_object,
        app,
    ):
        """Test that accessing a private package's utilization raises NotAuthorized"""
        from ckan.logic import NotAuthorized

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        # Mock package_show to raise NotAuthorized for private package
        mock_package_show = MagicMock(
            side_effect=NotAuthorized('User not authorized to view package')
        )
        mock_get_action.return_value = mock_package_show

        mock_args.get.side_effect = lambda x, default: {
            'id': resource['id'],
            'keyword': '',
            'disable_keyword': '',
            'organization': '',
        }.get(x, default)

        with pytest.raises(NotAuthorized):
            UtilizationController.search()

    @patch(
        'ckanext.feedback.controllers.utilization.current_user',
        new_callable=lambda: str,
    )
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_search_with_empty_id(
        self,
        mock_render,
        mock_args,
        mock_get_utilizations,
        mock_pagination,
        mock_page,
        mock_current_user_fixture,
    ):
        """Test search with empty id parameter to cover line 75"""
        keyword = 'keyword'
        disable_keyword = 'disable keyword'
        page = 1
        limit = 20
        offset = 0
        pager_url = 'utilization.search'

        mock_pagination.return_value = [page, limit, offset, pager_url]
        mock_args.get.side_effect = lambda x, default: {
            'id': '',  # Empty id to skip the if id: block
            'keyword': keyword,
            'disable_keyword': disable_keyword,
            'organization': '',
        }.get(x, default)
        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']
        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_details_with_utilization_not_found(
        self,
        mock_detail_service,
        mock_abort,
    ):
        """Test details method when utilization is not found to cover line 257"""
        from werkzeug.exceptions import NotFound

        utilization_id = 'non_existent_id'
        mock_detail_service.get_utilization.return_value = None
        # Make abort raise an exception to stop execution
        mock_abort.side_effect = NotFound()

        with pytest.raises(NotFound):
            UtilizationController.details(utilization_id)

        mock_abort.assert_called_once_with(404, _('Utilization not found'))

    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController'
        '._check_organization_admin_role'
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.current_user')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_approve_with_utilization_not_found(
        self,
        mock_detail_service,
        mock_current_user,
        mock_abort,
        mock_check_role,
        sysadmin,
        admin_context,
    ):
        """Test approve method when utilization is not found to cover line 314"""
        from werkzeug.exceptions import NotFound

        utilization_id = 'non_existent_id'

        # Mock _check_organization_admin_role to pass
        mock_check_role.return_value = None

        # Mock get_utilization to return None
        mock_detail_service.get_utilization.return_value = None
        mock_current_user.return_value = model.User.get(sysadmin['name'])
        # Make abort raise an exception to stop execution
        mock_abort.side_effect = NotFound()

        with admin_context:
            with pytest.raises(NotFound):
                UtilizationController.approve(utilization_id)

        mock_abort.assert_called_with(404, _('Utilization not found'))

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_check_organization_admin_role_with_utilization_not_found(
        self,
        mock_detail_service,
        mock_abort,
    ):
        from werkzeug.exceptions import NotFound

        utilization_id = 'non_existent_id'
        mock_detail_service.get_utilization.return_value = None
        # Make abort raise an exception to stop execution
        mock_abort.side_effect = NotFound()

        with pytest.raises(NotFound):
            UtilizationController._check_organization_admin_role(utilization_id)

        mock_abort.assert_called_once_with(
            404,
            _(
                'The requested URL was not found on the server. If you entered the'
                ' URL manually please check your spelling and try again.'
            ),
        )

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_new(
        self,
        mock_get_action,
        mock_args,
        mock_get_resource,
        mock_render,
        dataset,
        resource,
        user,
        organization,
        mock_resource_object,
        user_context,
    ):

        mock_args.get.side_effect = lambda x, default: {
            'resource_id': resource['id'],
            'return_to_resource': True,
        }.get(x, default)

        mock_package = {
            'id': dataset['id'],
            'name': 'test_package',
            'organization': {'name': organization['name']},
        }
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show

        mock_dataset = MagicMock()
        mock_dataset.id = dataset['id']
        mock_dataset.owner_org = organization['id']
        mock_resource = mock_resource_object(
            org_id=organization['id'], org_name=organization['name']
        )
        mock_get_resource.return_value = mock_resource

        UtilizationController.new()

        mock_get_action.assert_called_once_with('package_show')
        mock_package_show.assert_called_once()

        mock_render.assert_called_once_with(
            'utilization/new.html',
            {
                'pkg_dict': mock_package,
                'return_to_resource': True,
                'resource': mock_resource.Resource,
            },
        )
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_new_with_resource_id(
        self,
        mock_get_action,
        mock_args,
        mock_get_resource,
        mock_render,
        dataset,
        resource,
        user,
        organization,
        mock_resource_object,
        user_context,
    ):
        mock_package = {
            'id': dataset['id'],
            'name': 'test_package',
            'organization': {'name': organization['name']},
        }
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show
        mock_resource = mock_resource_object(
            org_id=organization['id'], org_name=organization['name']
        )
        mock_get_resource.return_value = mock_resource

        mock_args.get.side_effect = lambda x, default: {
            'title': 'title',
            'url': '',
            'description': 'description',
        }.get(x, default)

        UtilizationController.new(resource_id=resource['id'])
        mock_get_action.assert_called_once_with('package_show')
        mock_package_show.assert_called_once()

        mock_render.assert_called_once_with(
            'utilization/new.html',
            {
                'pkg_dict': mock_package,
                'return_to_resource': False,
                'resource': mock_resource.Resource,
            },
        )
        mock_render.assert_called_once()

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
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    def test_create_without_resource_id_title_description(
        self,
        mock_get_resource,
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
        mock_get_resource.return_value = None
        UtilizationController.create()

        mock_toolkit_abort.assert_called_once_with(400)
        mock_registration_service.create_utilization.assert_called_once_with(
            resource_id, title, url, description
        )
        mock_summary_service.create_utilization_summary.assert_called_once_with(
            resource_id
        )

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

    @patch('ckanext.feedback.controllers.utilization.get_action')
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
        mock_get_action,
        user,
        organization,
        mock_utilization_object,
        mock_resource_object,
        user_context,
    ):
        utilization_id = 'utilization id'

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
        mock_utilization.resource_id = 'mock_resource_id'
        mock_utilization.owner_org = 'mock_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        mock_detail_service.get_utilization_comments.return_value = [
            'comments',
            'total_count',
        ]
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization['id']

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
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
                'pkg_dict': {'id': 'mock_package'},
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
                'selected_category': 'REQUEST',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.get_action')
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
        mock_get_action,
        user,
        organization,
        mock_utilization_object,
        mock_resource_object,
        user_context,
    ):
        utilization_id = 'utilization id'
        organization_model = model.Group.get(organization['id'])

        member = model.Member(
            group=organization_model,
            group_id=organization['id'],
            table_id=user['id'],
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
        mock_utilization.resource_id = 'mock_resource_id'
        mock_utilization.owner_org = 'mock_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        mock_detail_service.get_utilization_comments.return_value = [
            'comments',
            'total_count',
        ]
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization['id']

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
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
                'pkg_dict': {'id': 'mock_package'},
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
                'selected_category': 'REQUEST',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.get_action')
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
        mock_get_action,
        organization,
        mock_resource_object,
    ):
        utilization_id = 'utilization id'

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
        mock_utilization.resource_id = 'mock_resource_id'
        mock_utilization.owner_org = 'mock_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        mock_detail_service.get_utilization_comments.return_value = [
            'comments',
            'total_count',
        ]
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization['id']
        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization'
        )
        mock_resource.package = mock_dataset
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
                'pkg_dict': {'id': 'mock_package'},
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
                'selected_category': 'REQUEST',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.get_action')
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
        mock_get_action,
        user,
        organization,
        user_context,
    ):
        utilization_id = 'utilization id'

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
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        mock_detail_service.get_utilization_comments.return_value = [
            'comments',
            'total_count',
        ]
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization['id']
        mock_resource = MagicMock()
        mock_resource.Resource = MagicMock()
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
                'pkg_dict': {'id': 'mock_package'},
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
                'selected_category': 'REQUEST',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_details_thank_with_user(
        self,
        mock_get_action,
        mock_render,
        mock_detail_service,
        mock_get_resource,
        mock_page,
        mock_pagination,
        user,
        organization,
        mock_utilization_object,
        mock_resource_object,
        user_context,
    ):
        utilization_id = 'utilization id'

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

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        mock_detail_service.get_utilization_comments.return_value = [
            'comments',
            'total_count',
        ]
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        mock_dataset = MagicMock()
        mock_dataset.owner_org = organization['id']

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='test_organization'
        )
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
                'pkg_dict': {'id': 'mock_package'},
                'categories': 'categories',
                'issue_resolutions': 'issue resolutions',
                'selected_category': 'THANK',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_approve(
        self,
        mock_get_action,
        mock_redirect_to,
        mock_session_commit,
        mock_summary_service,
        mock_detail_service,
        sysadmin,
        mock_current_user_fixture,
        admin_context,
    ):
        utilization_id = 'utilization id'
        resource_id = 'resource id'

        mock_utilization = MagicMock()
        mock_utilization.resource_id = resource_id
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show

        UtilizationController.approve(utilization_id)

        mock_detail_service.get_utilization.assert_any_call(utilization_id)
        mock_detail_service.approve_utilization.assert_called_once_with(
            utilization_id, sysadmin['id']
        )
        mock_summary_service.refresh_utilization_summary.assert_called_once_with(
            resource_id
        )
        mock_session_commit.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._upload_image'
    )
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
        mock_upload_image,
        mock_files,
        mock_form,
        mock_current_user_fixture,
    ):
        utilization_id = 'utilization id'
        category = UtilizationCommentCategory.REQUEST.name
        content = 'content'
        attached_image_filename = 'attached_image_filename'

        mock_form.get.side_effect = [category, content, attached_image_filename]

        mock_file = MagicMock()
        mock_file.filename = attached_image_filename
        mock_file.content_type = 'image/png'
        mock_file.read.return_value = b'fake image data'
        mock_files.return_value = mock_file

        mock_upload_image.return_value = attached_image_filename

        UtilizationController.create_comment(utilization_id)

        mock_detail_service.create_utilization_comment.assert_called_once_with(
            utilization_id, category, content, attached_image_filename
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._upload_image'
    )
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.UtilizationController.details')
    def test_create_comment_with_bad_image(
        self,
        mock_details,
        mock_flash_error,
        mock_upload_image,
        mock_files,
        mock_form,
    ):
        utilization_id = 'utilization id'
        category = 'category'
        content = 'content'
        attached_image_filename = 'attached_image_filename'

        mock_form.get.side_effect = [category, content, attached_image_filename]

        mock_file = MagicMock()
        mock_file.filename = 'bad_image.txt'
        mock_files.return_value = mock_file

        mock_upload_image.side_effect = toolkit.ValidationError(
            {'upload': ['Invalid image file type']}
        )

        UtilizationController.create_comment(utilization_id)

        mock_flash_error.assert_called_once_with(
            {'Upload': 'Invalid image file type'},
            allow_html=True,
        )
        mock_details.assert_called_once_with(utilization_id, category, content)

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._upload_image'
    )
    def test_create_comment_with_bad_image_exception(
        self,
        mock_upload_image,
        mock_files,
        mock_form,
    ):
        utilization_id = 'utilization id'
        category = 'category'
        content = 'content'
        attached_image_filename = 'attached_image_filename'

        mock_form.get.side_effect = [category, content, attached_image_filename]

        mock_file = MagicMock()
        mock_file.filename = attached_image_filename
        mock_file.content_type = 'image/png'
        mock_file.read.return_value = b'fake image data'
        mock_files.return_value = mock_file

        mock_upload_image.side_effect = Exception('Unexpected error')

        with pytest.raises(Exception):
            UtilizationController.create_comment(utilization_id)

        mock_upload_image.assert_called_once_with(mock_file)

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
        attached_image_filename = None

        mock_form.get.side_effect = [category, content, attached_image_filename]

        UtilizationController.create_comment(utilization_id)

        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    def test_create_comment_without_comment_length(
        self,
        mock_flash_flash_error,
        mock_redirect_to,
        mock_files,
        mock_form,
    ):
        utilization_id = 'utilization id'
        category = UtilizationCommentCategory.REQUEST.name
        content = 'ex'
        while True:
            content += content
            if 1000 < len(content):
                break
        attached_image_filename = None

        mock_form.get.side_effect = [category, content, attached_image_filename]

        mock_files.return_value = None

        UtilizationController.create_comment(utilization_id)

        mock_flash_flash_error.assert_called_once_with(
            'Please keep the comment length below 1000',
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with(
            'utilization.details',
            utilization_id=utilization_id,
            category=category,
            attached_image_filename=attached_image_filename,
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.UtilizationController.details')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    def test_create_comment_without_bad_recaptcha(
        self,
        mock_flash_error,
        mock_is_recaptcha_verified,
        mock_details,
        mock_files,
        mock_form,
    ):
        utilization_id = 'utilization_id'
        category = UtilizationCommentCategory.REQUEST.name
        content = 'content'
        attached_image_filename = None

        mock_form.get.side_effect = [
            category,
            content,
            attached_image_filename,
        ]

        mock_files.return_value = None

        mock_is_recaptcha_verified.return_value = False
        UtilizationController.create_comment(utilization_id)
        mock_details.assert_called_once_with(
            utilization_id, category, content, attached_image_filename
        )

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
        mock_utilization_object,
        mock_resource_object,
    ):
        utilization_id = 'utilization_id'
        category = 'category'
        content = 'comment_content'
        attached_image_filename = None
        softened = 'mock_softened'

        mock_suggest_ai_comment.return_value = softened

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        UtilizationController.suggested_comment(utilization_id, category, content)
        mock_render.assert_called_once_with(
            'utilization/suggestion.html',
            {
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'selected_category': category,
                'content': content,
                'attached_image_filename': attached_image_filename,
                'softened': softened,
                'action': MoralCheckAction,
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
        mock_utilization_object,
        mock_resource_object,
    ):
        utilization_id = 'utilization_id'
        category = 'category'
        content = 'comment_content'
        attached_image_filename = None
        softened = None

        mock_suggest_ai_comment.return_value = softened

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        UtilizationController.suggested_comment(utilization_id, category, content)
        mock_render.assert_called_once_with(
            'utilization/expect_suggestion.html',
            {
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'selected_category': category,
                'content': content,
                'attached_image_filename': attached_image_filename,
                'action': MoralCheckAction,
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
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._upload_image'
    )
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
        mock_upload_image,
        mock_files,
        mock_form,
        mock_method,
        mock_utilization_object,
        mock_resource_object,
    ):
        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        utilization_id = mock_utilization.id
        category = 'category'
        content = 'comment_content'
        attached_image_filename = 'attached_image_filename'

        config['ckan.feedback.moral_keeper_ai.enable'] = False

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'category': category,
            'comment-content': content,
            'attached_image_filename': attached_image_filename,
        }.get(x, default)

        mock_file = MagicMock()
        mock_file.filename = attached_image_filename
        mock_file.content_type = 'image/png'
        mock_file.read.return_value = b'fake image data'
        mock_files.return_value = mock_file

        mock_upload_image.return_value = attached_image_filename

        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
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
                'attached_image_filename': attached_image_filename,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._upload_image'
    )
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.UtilizationController.details')
    def test_check_comment_with_bad_image(
        self,
        mock_details,
        mock_flash_error,
        mock_upload_image,
        mock_files,
        mock_form,
        mock_method,
    ):
        utilization_id = 'utilization id'
        category = 'category'
        content = 'content'
        attached_image_filename = 'attached_image_filename'

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'category': category,
            'comment-content': content,
            'attached_image_filename': attached_image_filename,
        }.get(x, default)

        mock_file = MagicMock()
        mock_file.filename = 'bad_image.txt'
        mock_files.return_value = mock_file

        mock_upload_image.side_effect = toolkit.ValidationError(
            {'upload': ['Invalid image file type']}
        )

        UtilizationController.check_comment(utilization_id)

        mock_flash_error.assert_called_once_with(
            {'Upload': 'Invalid image file type'}, allow_html=True
        )
        mock_details.assert_called_once_with(utilization_id, category, content)

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._upload_image'
    )
    def test_check_comment_with_bad_image_exception(
        self,
        mock_upload_image,
        mock_files,
        mock_form,
        mock_method,
    ):
        utilization_id = 'utilization id'
        category = 'category'
        content = 'content'
        attached_image_filename = 'attached_image_filename'

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'category': category,
            'comment-content': content,
            'attached_image_filename': attached_image_filename,
        }.get(x, default)

        mock_file = MagicMock()
        mock_file.filename = attached_image_filename
        mock_file.content_type = 'image/png'
        mock_file.read.return_value = b'fake image data'
        mock_files.return_value = mock_file

        mock_upload_image.side_effect = Exception('Bad image')

        with pytest.raises(Exception):
            UtilizationController.check_comment(utilization_id)

        mock_upload_image.assert_called_once_with(mock_file)

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_utilization_comment_categories'
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.check_ai_comment')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.create_utilization_comment_moral_check_log'
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_check_comment_POST_judgement_True(
        self,
        mock_render,
        mock_create_utilization_comment_moral_check_log,
        mock_get_action,
        mock_check_ai_comment,
        mock_get_resource,
        mock_get_utilization,
        mock_get_utilization_comment_categories,
        mock_is_recaptcha_verified,
        mock_files,
        mock_form,
        mock_method,
        mock_utilization_object,
        mock_resource_object,
    ):
        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        utilization_id = mock_utilization.id
        category = 'category'
        content = 'comment_content'
        attached_image_filename = None
        judgement = True

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'category': category,
            'comment-content': content,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': False,
        }.get(x, default)

        mock_files.return_value = None

        mock_check_ai_comment.return_value = judgement

        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show

        mock_create_utilization_comment_moral_check_log.return_value = None

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
                'attached_image_filename': attached_image_filename,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    @patch(
        'ckanext.feedback.services.common.config.BaseConfig.is_enable',
        return_value=True,
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
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
        mock_files,
        mock_form,
        mock_method,
        mock_render,
        mock_is_enable,
        mock_FeedbackConfig,
        mock_utilization_object,
        mock_resource_object,
    ):
        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        utilization_id = mock_utilization.id
        category = 'category'
        content = 'comment_content'
        attached_image_filename = None
        judgement = False

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_check_ai_comment.return_value = judgement
        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'category': category,
            'comment-content': content,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': False,
        }.get(x, default)

        mock_files.return_value = None
        mock_is_recaptcha_verified.return_value = True

        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show

        mock_get_utilization_comment_categories.return_value = 'mock_categories'

        UtilizationController.check_comment(utilization_id)
        mock_check_ai_comment.assert_called_once_with(comment=content)
        mock_suggested_comment.assert_called_once_with(
            utilization_id=utilization_id,
            category=category,
            content=content,
            attached_image_filename=attached_image_filename,
        )
        mock_render.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_utilization_comment_categories'
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.create_utilization_comment_moral_check_log'
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_check_comment_POST_suggested(
        self,
        mock_render,
        mock_create_utilization_comment_moral_check_log,
        mock_get_action,
        mock_get_resource,
        mock_get_utilization,
        mock_get_utilization_comment_categories,
        mock_is_recaptcha_verified,
        mock_files,
        mock_form,
        mock_method,
        mock_utilization_object,
        mock_resource_object,
    ):
        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        utilization_id = mock_utilization.id
        category = 'category'
        content = 'comment_content'
        attached_image_filename = None

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'category': category,
            'comment-content': content,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': 'True',
            'action': MoralCheckAction.INPUT_SELECTED,
            'input-comment': 'test_input_comment',
            'suggested-comment': 'test_suggested_comment',
        }.get(x, default)

        mock_files.return_value = None

        mock_get_utilization.return_value = mock_utilization
        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show

        mock_create_utilization_comment_moral_check_log.return_value = None

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
                'attached_image_filename': attached_image_filename,
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
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.UtilizationController.details')
    def test_check_comment_POST_bad_recaptcha(
        self,
        mock_details,
        mock_flash_error,
        mock_is_recaptcha_verified,
        mock_files,
        mock_form,
        mock_method,
    ):
        utilization_id = 'utilization_id'
        category = 'category'
        content = 'comment_content'
        attached_image_filename = None

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'category': category,
            'comment-content': content,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': True,
        }.get(x, default)

        mock_files.return_value = None

        mock_is_recaptcha_verified.return_value = False

        UtilizationController.check_comment(utilization_id)
        mock_flash_error.assert_called_once_with(
            'Bad Captcha. Please try again.', allow_html=True
        )
        mock_details.assert_called_once_with(
            utilization_id, category, content, attached_image_filename
        )

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_check_comment_POST_without_validate_comment(
        self,
        mock_redirect_to,
        mock_flash_error,
        mock_is_recaptcha_verified,
        mock_files,
        mock_form,
        mock_method,
    ):
        utilization_id = 'utilization_id'
        category = 'category'
        content = 'comment_content'
        while len(content) < 1000:
            content += content
        attached_image_filename = None

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'category': category,
            'comment-content': content,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': True,
        }.get(x, default)

        mock_files.return_value = None

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
            attached_image_filename=attached_image_filename,
        )

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    def test_check_attached_image(
        self,
        mock_send_file,
        mock_detail_service,
    ):
        utilization_id = 'utilization id'
        attached_image_filename = 'attached_image_filename'

        mock_detail_service.get_attached_image_path.return_value = 'attached_image_path'

        UtilizationController.check_attached_image(
            utilization_id, attached_image_filename
        )

        mock_detail_service.get_attached_image_path.assert_called_once_with(
            attached_image_filename
        )
        mock_send_file.assert_called_once_with('attached_image_path')

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_approve_comment(
        self,
        mock_get_action,
        mock_redirect_to,
        mock_session_commit,
        mock_detail_service,
        admin_context,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'

        UtilizationController.approve_comment(utilization_id, comment_id)

        mock_detail_service.approve_utilization_comment.assert_called_once_with(
            comment_id, admin_context.return_value.id
        )
        mock_detail_service.refresh_utilization_comments.assert_called_once_with(
            utilization_id
        )
        mock_session_commit.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_edit(
        self,
        mock_get_action,
        mock_detail_service,
        mock_get_resource,
        mock_edit_service,
        mock_render,
        mock_utilization_object,
        mock_resource_object,
        admin_context,
    ):
        utilization_id = 'test utilization id'
        utilization_details = MagicMock()
        resource_details = MagicMock()

        mock_edit_service.get_utilization_details.return_value = utilization_details
        mock_edit_service.get_resource_details.return_value = resource_details

        utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_detail_service.get_utilization.return_value = utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='test_organization'
        )
        mock_get_resource.return_value = mock_resource

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
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_update(
        self,
        mock_get_action,
        mock_detail_service,
        mock_redirect_to,
        mock_flash_success,
        mock_session_commit,
        mock_edit_service,
        mock_form,
        organization,
        admin_context,
    ):
        utilization_id = 'utilization id'
        url = 'https://example.com'
        title = 'title'
        description = 'description'

        mock_form.get.side_effect = [title, url, description]

        utilization = MagicMock()
        utilization.owner_org = organization['id']
        utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        UtilizationController.update(utilization_id)

        mock_edit_service.update_utilization.assert_called_once_with(
            utilization_id, title, url, description
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_update_without_title_description(
        self,
        mock_get_action,
        mock_detail_service,
        mock_toolkit_abort,
        mock_flash_success,
        mock_edit_service,
        mock_form,
        organization,
        admin_context,
    ):
        utilization_id = 'test_utilization_id'
        title = ''
        url = ''
        description = ''

        mock_form.get.side_effect = [title, url, description]

        utilization = MagicMock()
        utilization.owner_org = organization['id']
        utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        UtilizationController.update(utilization_id)

        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_update_with_invalid_title_length(
        self,
        mock_get_action,
        mock_detail_service,
        mock_flash_error,
        mock_redirect_to,
        mock_form,
        organization,
        admin_context,
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

        utilization = MagicMock()
        utilization.owner_org = organization['id']
        utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        UtilizationController.update(utilization_id)

        mock_flash_error.assert_called_once_with(
            'Please keep the title length below 50',
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with(
            'utilization.edit',
            utilization_id=utilization_id,
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_update_without_url(
        self,
        mock_get_action,
        mock_detail_service,
        mock_flash_error,
        mock_redirect_to,
        mock_form,
        organization,
        admin_context,
    ):
        utilization_id = 'utilization id'
        url = 'test_url'
        title = 'title'
        description = 'description'

        mock_form.get.side_effect = [title, url, description]

        utilization = MagicMock()
        utilization.owner_org = organization['id']
        utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        UtilizationController.update(utilization_id)

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.edit',
            utilization_id=utilization_id,
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_update_with_invalid_description_length(
        self,
        mock_get_action,
        mock_detail_service,
        mock_flash_error,
        mock_redirect_to,
        mock_form,
        organization,
        admin_context,
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

        utilization = MagicMock()
        utilization.owner_org = organization['id']
        utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        UtilizationController.update(utilization_id)

        mock_flash_error.assert_called_once_with(
            'Please keep the description length below 2000',
            allow_html=True,
        )
        mock_redirect_to.assert_called_once_with(
            'utilization.edit',
            utilization_id=utilization_id,
        )

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_delete(
        self,
        mock_get_action,
        mock_redirect_to,
        mock_flash_success,
        mock_session_commit,
        mock_summary_service,
        mock_edit_service,
        mock_detail_service,
        admin_context,
    ):
        utilization_id = 'utilization id'
        resource_id = 'resource id'

        utilization = MagicMock()
        utilization.resource_id = resource_id
        mock_detail_service.get_utilization.return_value = utilization

        UtilizationController.delete(utilization_id)

        mock_detail_service.get_utilization.assert_any_call(utilization_id)
        mock_edit_service.delete_utilization.assert_called_once_with(utilization_id)
        mock_summary_service.refresh_utilization_summary.assert_called_once_with(
            resource_id
        )
        assert mock_session_commit.call_count == 2
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once_with('utilization.search')

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_create_issue_resolution(
        self,
        mock_get_action,
        mock_redirect_to,
        mock_session_commit,
        mock_summary_service,
        mock_detail_service,
        mock_form,
        admin_context,
    ):
        utilization_id = 'utilization id'
        description = 'description'

        mock_form.get.return_value = description

        UtilizationController.create_issue_resolution(utilization_id)

        mock_detail_service.create_issue_resolution.assert_called_once_with(
            utilization_id, description, admin_context.return_value.id
        )
        mock_summary_service.increment_issue_resolution_summary.assert_called_once_with(
            utilization_id
        )
        mock_session_commit.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_create_issue_resolution_without_description(
        self,
        mock_get_action,
        mock_redirect_to,
        mock_summary_service,
        mock_detail_service,
        mock_form,
        mock_abort,
        admin_context,
    ):
        utilization_id = 'utilization id'
        description = ''

        mock_utilization = MagicMock()
        mock_utilization.owner_org = 'test_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show

        mock_form.get.return_value = description
        mock_redirect_to.return_value = ''

        with admin_context.test_request_context():
            UtilizationController.create_issue_resolution(utilization_id)

        mock_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.os.path.exists')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_attached_image_with_sysadmin(
        self,
        mock_get_action,
        mock_send_file,
        mock_exists,
        mock_detail_service,
        admin_context,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        attached_image_filename = 'attached_image_filename'

        mock_detail_service.get_utilization.return_value = MagicMock()
        mock_detail_service.get_utilization_comment.return_value = 'mock_comment'
        mock_detail_service.get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = True

        UtilizationController.attached_image(
            utilization_id, comment_id, attached_image_filename
        )

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comment.assert_called_once_with(
            comment_id, utilization_id, None, attached_image_filename
        )
        mock_detail_service.get_attached_image_path.assert_called_once_with(
            attached_image_filename
        )
        mock_exists.assert_called_once_with('attached_image_path')
        mock_send_file.assert_called_once_with('attached_image_path')

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.os.path.exists')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_attached_image_with_user(
        self,
        mock_get_action,
        mock_send_file,
        mock_exists,
        mock_detail_service,
        admin_context,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        attached_image_filename = 'attached_image_filename'

        mock_detail_service.get_utilization.return_value = MagicMock()
        mock_detail_service.get_utilization_comment.return_value = 'mock_comment'
        mock_detail_service.get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = True

        UtilizationController.attached_image(
            utilization_id, comment_id, attached_image_filename
        )

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comment.assert_called_once_with(
            comment_id, utilization_id, None, attached_image_filename
        )
        mock_detail_service.get_attached_image_path.assert_called_once_with(
            attached_image_filename
        )
        mock_exists.assert_called_once_with('attached_image_path')
        mock_send_file.assert_called_once_with('attached_image_path')

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.os.path.exists')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_attached_image_with_not_found_attached_image(
        self,
        mock_get_action,
        mock_send_file,
        mock_exists,
        mock_detail_service,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        attached_image_filename = 'attached_image_filename'

        mock_detail_service.get_utilization.return_value = MagicMock()
        mock_detail_service.get_utilization_comment.return_value = 'mock_comment'
        mock_detail_service.get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = False

        with pytest.raises(NotFound):
            UtilizationController.attached_image(
                utilization_id, comment_id, attached_image_filename
            )

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comment.assert_called_once_with(
            comment_id, utilization_id, None, attached_image_filename
        )
        mock_detail_service.get_attached_image_path.assert_called_once_with(
            attached_image_filename
        )
        mock_exists.assert_called_once_with('attached_image_path')
        mock_send_file.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.os.path.exists')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_attached_image_with_not_found_comment(
        self,
        mock_get_action,
        mock_send_file,
        mock_exists,
        mock_detail_service,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        attached_image_filename = 'attached_image_filename'

        mock_detail_service.get_utilization.return_value = MagicMock()
        mock_detail_service.get_utilization_comment.return_value = None

        with pytest.raises(NotFound):
            UtilizationController.attached_image(
                utilization_id, comment_id, attached_image_filename
            )

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comment.assert_called_once_with(
            comment_id, utilization_id, None, attached_image_filename
        )
        mock_detail_service.get_attached_image_path.assert_not_called()
        mock_exists.assert_not_called()
        mock_send_file.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.os.path.exists')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    def test_attached_image_with_not_found_utilization(
        self,
        mock_send_file,
        mock_exists,
        mock_detail_service,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        attached_image_filename = 'attached_image_filename'

        mock_detail_service.get_utilization.return_value = None

        with pytest.raises(NotFound):
            UtilizationController.attached_image(
                utilization_id, comment_id, attached_image_filename
            )

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comment.assert_not_called()
        mock_detail_service.get_attached_image_path.assert_not_called()
        mock_exists.assert_not_called()
        mock_send_file.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch(
        'ckanext.feedback.controllers.utilization.current_user.sysadmin',
        return_value=True,
    )
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_check_organization_adimn_role_with_sysadmin(
        self,
        mock_get_action,
        mock_current_user_fixture_sysadmin,
        mocked_detail_service,
        mock_toolkit_abort,
        sysadmin,
        admin_context,
    ):

        organization_id = 'organization id'

        mocked_utilization = MagicMock()
        mocked_utilization.owner_org = organization_id
        mocked_utilization.package_id = 'mock_package_id'
        mocked_detail_service.get_utilization.return_value = mocked_utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show

        with admin_context:
            UtilizationController._check_organization_admin_role('utilization_id')

        mock_toolkit_abort.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckan.model.Group.get')
    @patch('ckanext.feedback.controllers.utilization.has_organization_admin_role')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_check_organization_adimn_role_with_org_admin(
        self,
        mock_get_action,
        mock_has_organization_admin_role,
        mock_get_group,
        mocked_detail_service,
        mock_toolkit_abort,
        sysadmin,
        admin_context,
    ):
        organization_id = 'test_org_id'
        organization_model = MagicMock()
        organization_model.id = organization_id
        mock_get_group.return_value = organization_model

        mocked_utilization = MagicMock()
        mocked_detail_service.get_utilization.return_value = mocked_utilization
        mocked_utilization.owner_org = organization_id
        mocked_utilization.package_id = 'mock_package_id'
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show

        mock_has_organization_admin_role.return_value = True

        with admin_context:
            UtilizationController._check_organization_admin_role('utilization_id')
        mock_toolkit_abort.assert_not_called()
        mock_has_organization_admin_role.assert_called_once_with(organization_id)

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckan.model.Group.get')
    @patch('ckanext.feedback.controllers.utilization.has_organization_admin_role')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_check_organization_adimn_role_with_user(
        self,
        mock_get_action,
        mock_has_organization_admin_role,
        mock_get_group,
        mocked_detail_service,
        mock_toolkit_abort,
        user,
        user_context,
    ):
        organization_id = 'test_org_id'
        organization_model = MagicMock()
        organization_model.id = organization_id
        mock_get_group.return_value = organization_model

        mocked_utilization = MagicMock()
        mocked_detail_service.get_utilization.return_value = mocked_utilization
        mocked_utilization.owner_org = organization_id
        mocked_utilization.package_id = 'mock_package_id'
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show

        mock_has_organization_admin_role.return_value = False

        with user_context:
            UtilizationController._check_organization_admin_role('utilization_id')
        mock_toolkit_abort.assert_called_once_with(
            404,
            _(
                'The requested URL was not found on the server. If you entered the URL'
                ' manually please check your spelling and try again.'
            ),
        )

    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_upload_destination'
    )
    @patch('ckanext.feedback.controllers.utilization.get_uploader')
    def test_upload_image(
        self,
        mock_get_uploader,
        mock_get_upload_destination,
    ):
        mock_image = MagicMock()
        mock_image.filename = 'test.png'

        mock_get_upload_destination.return_value = '/test/upload/path'

        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = 'test_image.png'

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        UtilizationController._upload_image(mock_image)

        mock_get_upload_destination.assert_called_once()
        mock_get_uploader.assert_called_once_with('/test/upload/path')
        mock_uploader.update_data_dict.assert_called_once()
        mock_uploader.upload.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.registration_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.send_email')
    @patch('ckanext.feedback.controllers.utilization.log.exception')
    def test_create_with_email_exception(
        self,
        mock_log_exception,
        mock_send_email,
        mock_get_resource,
        mock_redirect_to,
        mock_flash_success,
        mock_session_commit,
        mock_summary_service,
        mock_registration_service,
        mock_form,
        mock_utilization_object,
        mock_resource_object,
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

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_registration_service.create_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        mock_send_email.side_effect = Exception('Test email exception')
        UtilizationController.create()

        mock_log_exception.assert_called_once_with(
            'Send email failed, for feedback notification.'
        )

        mock_registration_service.create_utilization.assert_called_with(
            resource_id, title, url, description
        )
        mock_summary_service.create_utilization_summary.assert_called_with(resource_id)
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource.read', id=package_name, resource_id=resource_id
        )

    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.current_user')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_details_without_user(
        self,
        mock_get_action,
        mock_current_user,
        mock_render,
        mock_detail_service,
        mock_get_resource,
        mock_page_cls,
        mock_get_pagination_value,
        admin_context,
        organization,
        mock_utilization_object,
        mock_resource_object,
    ):
        utilization_id = 'utilization id'

        page = 1
        limit = 20
        offset = 0
        pager_url = ''

        mock_get_pagination_value.return_value = [page, limit, offset, pager_url]

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        mock_detail_service.get_utilization_comments.return_value = [
            'comments',
            'total_count',
        ]
        mock_detail_service.get_utilization_comment_categories.return_value = (
            'categories'
        )
        mock_detail_service.get_issue_resolutions.return_value = 'issue resolutions'

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='test_organization'
        )
        mock_get_resource.return_value = mock_resource
        mock_page_cls.return_value = 'mock_page'
        UtilizationController.details(utilization_id)
        mock_get_pagination_value.assert_called_once_with('utilization.details')

    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    @patch(
        'ckanext.feedback.services.common.config.BaseConfig.is_enable',
        return_value=True,
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.check_ai_comment')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.'
        'get_utilization_comment_categories'
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_check_comment_POST_ai_disabled(
        self,
        mock_get_action,
        mock_get_resource,
        mock_get_utilization,
        mock_get_utilization_comment_categories,
        mock_check_ai_comment,
        mock_is_recaptcha_verified,
        mock_files,
        mock_form,
        mock_method,
        mock_render,
        mock_is_enable,
        mock_FeedbackConfig,
        mock_utilization_object,
        mock_resource_object,
    ):
        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        utilization_id = mock_utilization.id
        category = 'category'
        content = 'comment_content'
        attached_image_filename = None

        mock_check_ai_comment.return_value = False

        mock_moral_keeper_ai = MagicMock()
        mock_moral_keeper_ai.is_enable.return_value = False
        mock_FeedbackConfig.return_value.moral_keeper_ai = mock_moral_keeper_ai

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'category': category,
            'comment-content': content,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': False,
        }.get(x, default)

        mock_files.return_value = None
        mock_is_recaptcha_verified.return_value = True

        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show

        mock_get_utilization_comment_categories.return_value = 'mock_categories'

        UtilizationController.check_comment(utilization_id)

        mock_check_ai_comment.assert_not_called()

        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.os.path.exists')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_attached_image_file_not_found(
        self,
        mock_get_action,
        mock_send_file,
        mock_exists,
        mock_detail_service,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        attached_image_filename = 'attached_image_filename'

        mock_detail_service.get_utilization.return_value = MagicMock()
        mock_detail_service.get_utilization_comment.return_value = 'mock_comment'
        mock_detail_service.get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = False

        with pytest.raises(NotFound):
            UtilizationController.attached_image(
                utilization_id, comment_id, attached_image_filename
            )

        mock_detail_service.get_utilization.assert_called_once_with(utilization_id)
        mock_detail_service.get_utilization_comment.assert_called_once_with(
            comment_id, utilization_id, None, attached_image_filename
        )
        mock_detail_service.get_attached_image_path.assert_called_once_with(
            attached_image_filename
        )
        mock_exists.assert_called_once_with('attached_image_path')
        mock_send_file.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.os.path.exists')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    @patch('ckanext.feedback.controllers.utilization.current_user')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_attached_image_with_current_user_not_model_user(
        self,
        mock_get_action,
        mock_current_user_fixture,
        mock_send_file,
        mock_exists,
        mock_detail_service,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        attached_image_filename = 'attached_image_filename'

        mock_current_user_fixture.__class__ = object
        mock_current_user_fixture.__instance_of__ = lambda x: False

        mock_detail_service.get_utilization.return_value = MagicMock()
        mock_detail_service.get_utilization_comment.return_value = 'mock_comment'
        mock_detail_service.get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = True

        UtilizationController.attached_image(
            utilization_id, comment_id, attached_image_filename
        )

        mock_detail_service.get_utilization_comment.assert_called_once_with(
            comment_id, utilization_id, True, attached_image_filename
        )
        mock_detail_service.get_attached_image_path.assert_called_once_with(
            attached_image_filename
        )
        mock_exists.assert_called_once_with('attached_image_path')
        mock_send_file.assert_called_once_with('attached_image_path')

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.os.path.exists')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    @patch('ckanext.feedback.controllers.utilization.current_user')
    @patch('ckanext.feedback.controllers.utilization.has_organization_admin_role')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_attached_image_with_org_admin(
        self,
        mock_get_action,
        mock_has_organization_admin_role,
        mock_current_user,
        mock_send_file,
        mock_exists,
        mock_detail_service,
        user,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        attached_image_filename = 'attached_image_filename'

        mock_current_user.__class__ = model.User

        mock_has_organization_admin_role.return_value = True

        mock_utilization = MagicMock()
        mock_utilization.owner_org = 'test_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        mock_detail_service.get_utilization_comment.return_value = 'mock_comment'
        mock_detail_service.get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = True

        UtilizationController.attached_image(
            utilization_id, comment_id, attached_image_filename
        )

        mock_detail_service.get_utilization_comment.assert_called_once_with(
            comment_id, utilization_id, None, attached_image_filename
        )
        mock_detail_service.get_attached_image_path.assert_called_once_with(
            attached_image_filename
        )
        mock_exists.assert_called_once_with('attached_image_path')
        mock_send_file.assert_called_once_with('attached_image_path')

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.os.path.exists')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    @patch('ckanext.feedback.controllers.utilization.current_user')
    @patch('ckanext.feedback.controllers.utilization.has_organization_admin_role')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_attached_image_with_normal_user(
        self,
        mock_get_action,
        mock_has_organization_admin_role,
        mock_current_user,
        mock_send_file,
        mock_exists,
        mock_detail_service,
        user,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        attached_image_filename = 'attached_image_filename'

        mock_current_user.__class__ = model.User
        mock_current_user.sysadmin = False

        mock_has_organization_admin_role.return_value = False

        mock_utilization = MagicMock()
        mock_utilization.owner_org = 'test_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_package_show = MagicMock(return_value={'id': 'mock_package'})
        mock_get_action.return_value = mock_package_show
        mock_detail_service.get_utilization_comment.return_value = 'mock_comment'
        mock_detail_service.get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = True

        UtilizationController.attached_image(
            utilization_id, comment_id, attached_image_filename
        )

        mock_detail_service.get_utilization_comment.assert_called_once_with(
            comment_id, utilization_id, True, attached_image_filename
        )
        mock_detail_service.get_attached_image_path.assert_called_once_with(
            attached_image_filename
        )
        mock_exists.assert_called_once_with('attached_image_path')
        mock_send_file.assert_called_once_with('attached_image_path')

    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.check_ai_comment')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController.'
        'suggested_comment'
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.'
        'get_utilization_comment_categories'
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    def test_check_comment_POST_ai_check_false(
        self,
        mock_get_action,
        mock_get_resource,
        mock_get_utilization,
        mock_get_utilization_comment_categories,
        mock_suggested_comment,
        mock_check_ai_comment,
        mock_is_recaptcha_verified,
        mock_files,
        mock_form,
        mock_method,
        mock_render,
        mock_FeedbackConfig,
        mock_utilization_object,
        mock_resource_object,
    ):
        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        utilization_id = mock_utilization.id
        category = 'category'
        content = 'comment_content'
        attached_image_filename = None

        mock_check_ai_comment.return_value = False

        mock_moral_keeper_ai = MagicMock()
        mock_moral_keeper_ai.is_enable.return_value = True
        mock_FeedbackConfig.return_value.moral_keeper_ai = mock_moral_keeper_ai

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'category': category,
            'comment-content': content,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': False,
        }.get(x, default)

        mock_files.return_value = None
        mock_is_recaptcha_verified.return_value = True

        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        mock_suggested_comment.return_value = 'mock_suggested_comment_result'
        result = UtilizationController.check_comment(utilization_id)
        mock_check_ai_comment.assert_called_once_with(comment=content)
        mock_suggested_comment.assert_called_once_with(
            utilization_id=utilization_id,
            category=category,
            content=content,
            attached_image_filename=attached_image_filename,
        )
        assert result == 'mock_suggested_comment_result'
        mock_render.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.check_ai_comment')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'UtilizationController.suggested_comment'
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.get_utilization_comment_categories'
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.get_action')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.create_utilization_comment_moral_check_log'
    )
    def test_check_comment_post_ai_check_true(
        self,
        mock_create_utilization_comment_moral_check_log,
        mock_get_action,
        mock_get_resource,
        mock_get_utilization,
        mock_get_utilization_comment_categories,
        mock_suggested_comment,
        mock_check_ai_comment,
        mock_is_recaptcha_verified,
        mock_files,
        mock_form,
        mock_method,
        mock_render,
        mock_FeedbackConfig,
        mock_utilization_object,
        mock_resource_object,
    ):
        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        utilization_id = mock_utilization.id
        category = 'category'
        content = 'comment_content'
        attached_image_filename = None

        mock_check_ai_comment.return_value = True

        mock_moral_keeper_ai = MagicMock()
        mock_moral_keeper_ai.is_enable.return_value = True
        mock_FeedbackConfig.return_value.moral_keeper_ai = mock_moral_keeper_ai

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'category': category,
            'comment-content': content,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': False,
        }.get(x, default)

        mock_files.return_value = None
        mock_is_recaptcha_verified.return_value = True

        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show

        mock_get_utilization_comment_categories.return_value = 'mock_categories'

        mock_create_utilization_comment_moral_check_log.return_value = None
        mock_render.return_value = 'mock_render_result'

        result = UtilizationController.check_comment(utilization_id)

        mock_check_ai_comment.assert_called_once_with(comment=content)
        mock_create_utilization_comment_moral_check_log.assert_called_once_with(
            utilization_id=utilization_id,
            action=MoralCheckAction.CHECK_COMPLETED.name,
            input_comment=content,
            suggested_comment=None,
            output_comment=content,
        )

        mock_suggested_comment.assert_not_called()
        mock_render.assert_called_once_with(
            'utilization/comment_check.html',
            {
                'pkg_dict': mock_package,
                'utilization_id': utilization_id,
                'utilization': mock_utilization,
                'content': content,
                'selected_category': category,
                'categories': 'mock_categories',
                'attached_image_filename': attached_image_filename,
            },
        )

        assert result == 'mock_render_result'


@pytest.mark.usefixtures('with_request_context')
@pytest.mark.db_test
class TestUtilizationCreatePreviousLog:
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_resource_by_utilization_id'
    )
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.create_utilization_comment_moral_check_log'
    )
    def test_create_previous_log_moral_keeper_ai_disabled(
        self,
        mock_create_utilization_comment_moral_check_log,
        mock_get_resource,
        utilization,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = False

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource.return_value = resource

        return_value = UtilizationController.create_previous_log(utilization.id)

        mock_create_utilization_comment_moral_check_log.assert_not_called()
        assert return_value == ('', 204)

    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_resource_by_utilization_id'
    )
    @patch('ckanext.feedback.controllers.utilization.request.get_json')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.create_utilization_comment_moral_check_log'
    )
    def test_create_previous_log_previous_type_suggestion(
        self,
        mock_create_utilization_comment_moral_check_log,
        mock_get_json,
        mock_get_resource,
        utilization,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = True

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource.return_value = resource
        mock_get_json.return_value = {
            'previous_type': 'suggestion',
            'input_comment': 'test_input_comment',
            'suggested_comment': 'test_suggested_comment',
        }
        mock_create_utilization_comment_moral_check_log.return_value = None

        return_value = UtilizationController.create_previous_log(utilization.id)

        mock_create_utilization_comment_moral_check_log.assert_called_once_with(
            utilization_id=utilization.id,
            action=MoralCheckAction.PREVIOUS_SUGGESTION.name,
            input_comment='test_input_comment',
            suggested_comment='test_suggested_comment',
            output_comment=None,
        )
        assert return_value == ('', 204)

    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_resource_by_utilization_id'
    )
    @patch('ckanext.feedback.controllers.utilization.request.get_json')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.create_utilization_comment_moral_check_log'
    )
    def test_create_previous_log_previous_type_confirm(
        self,
        mock_create_utilization_comment_moral_check_log,
        mock_get_json,
        mock_get_resource,
        utilization,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = True

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource.return_value = resource
        mock_get_json.return_value = {
            'previous_type': 'confirm',
            'input_comment': 'test_input_comment',
            'suggested_comment': 'test_suggested_comment',
        }
        mock_create_utilization_comment_moral_check_log.return_value = None

        return_value = UtilizationController.create_previous_log(utilization.id)

        mock_create_utilization_comment_moral_check_log.assert_called_once_with(
            utilization_id=utilization.id,
            action=MoralCheckAction.PREVIOUS_CONFIRM.name,
            input_comment='test_input_comment',
            suggested_comment='test_suggested_comment',
            output_comment=None,
        )
        assert return_value == ('', 204)

    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_resource_by_utilization_id'
    )
    @patch('ckanext.feedback.controllers.utilization.request.get_json')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.create_utilization_comment_moral_check_log'
    )
    def test_create_previous_log_previous_type_none(
        self,
        mock_create_utilization_comment_moral_check_log,
        mock_get_json,
        mock_get_resource,
        utilization,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = True

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource.return_value = resource
        mock_get_json.return_value = {
            'previous_type': 'none',
            'input_comment': 'test_input_comment',
            'suggested_comment': 'test_suggested_comment',
        }

        return_value = UtilizationController.create_previous_log(utilization.id)

        mock_create_utilization_comment_moral_check_log.assert_not_called()
        assert return_value == ('', 204)
