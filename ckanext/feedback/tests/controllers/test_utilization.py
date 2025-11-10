from unittest.mock import MagicMock, patch

import pytest
from ckan import model
from ckan.common import _, config
from ckan.plugins import toolkit
from werkzeug.exceptions import NotFound

from ckanext.feedback.controllers.utilization import UtilizationController
from ckanext.feedback.models.types import MoralCheckAction
from ckanext.feedback.models.utilization import UtilizationCommentCategory

engine = model.repo.session.get_bind()

TEST_UTILIZATION_ID = 'test-utilization-id'
TEST_REPLY_ID = 'test-reply-id'
TEST_IMAGE_FILENAME = 'test-image.png'
TEST_COMMENT_ID = 'test-comment-id'
TEST_RESOURCE_ID = 'test-resource-id'
TEST_PACKAGE_NAME = 'test-package'
TEST_ORGANIZATION_ID = 'test-org-id'
TEST_CONTENT = 'test-content'
TEST_TITLE = 'test-title'
TEST_DESCRIPTION = 'test-description'
TEST_URL = 'https://example.com'


@pytest.mark.db_test
@pytest.mark.usefixtures("admin_context")
class TestUtilizationController:

    # Helper methods to reduce test duplication
    def _setup_mock_utilization(
        self, mock_detail_service, owner_org=TEST_ORGANIZATION_ID
    ):
        """Helper to setup mock utilization object"""
        mock_utilization = MagicMock(owner_org=owner_org)
        mock_detail_service.get_utilization.return_value = mock_utilization
        return mock_utilization

    def _assert_approve_reply_common(
        self, mock_redirect, mock_commit=None, should_commit=True
    ):
        """Helper to assert common approve_reply behavior"""
        mock_redirect.assert_called_once()
        if mock_commit:
            if should_commit:
                mock_commit.assert_called_once()
            else:
                mock_commit.assert_not_called()

    def _setup_mock_form_get(self, values_dict):
        """Helper to setup mock form.get with lambda"""
        return lambda x, default=None: values_dict.get(x, default)

    @patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
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
        mock_require_resource_package_access,
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
            'resource_id': resource['id'],
            'package_id': '',
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        mock_get_resource.assert_called_once_with(resource['id'])
        mock_require_resource_package_access.assert_called_once()

        mock_get_utilizations.assert_called_once_with(
            resource_id=resource['id'],
            package_id='',
            keyword=keyword,
            approval=None,
            admin_owner_orgs=None,
            org_name='',
            limit=limit,
            offset=offset,
            user_orgs='all',
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

    @patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
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
        mock_require_resource_package_access,
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
        mock_require_resource_package_access.return_value = {'id': 'mock_package'}

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
            'resource_id': '',
            'package_id': dataset['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
            'organization': organization_model.name,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource_id='',
            package_id=dataset['id'],
            keyword=keyword,
            approval=None,
            admin_owner_orgs=[organization['id']],
            org_name='test organization',
            limit=limit,
            offset=offset,
            user_orgs=[organization['id']],
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

    @patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
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
        mock_require_resource_package_access,
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
        mock_require_resource_package_access.return_value = {'id': 'mock_package'}

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
            'resource_id': '',
            'package_id': dataset['id'],
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource_id='',
            package_id=dataset['id'],
            keyword=keyword,
            approval=True,
            admin_owner_orgs=None,
            org_name='',
            limit=limit,
            offset=offset,
            user_orgs=[],
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

    @patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
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
        mock_require_resource_package_access,
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
        mock_require_resource_package_access.return_value = {'id': 'mock_package'}
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
            'resource_id': resource['id'],
            'package_id': '',
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        mock_get_resource.assert_called_once_with(resource['id'])
        mock_require_resource_package_access.assert_called_once()

        mock_get_utilizations.assert_called_once_with(
            resource_id=resource['id'],
            package_id='',
            keyword=keyword,
            approval=True,
            admin_owner_orgs=None,
            org_name='',
            limit=limit,
            offset=offset,
            user_orgs=None,
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

    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    @patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
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
        mock_require_resource_package_access,
        mock_require_package_access,
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
        mock_require_package_access.return_value = {'id': 'mock_package'}

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
            'resource_id': '',
            'package_id': mock_dataset.id,
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource_id='',
            package_id=mock_dataset.id,
            keyword=keyword,
            approval=None,
            admin_owner_orgs=None,
            org_name='',
            limit=limit,
            offset=offset,
            user_orgs='all',
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

    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    @patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
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
        mock_require_resource_package_access,
        mock_require_package_access,
    ):
        mock_get_resource.return_value = None
        mock_package_get.return_value = None
        mock_require_package_access.return_value = {'id': 'mock_package'}

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
            'resource_id': '',
            'package_id': '',
            'keyword': keyword,
            'disable_keyword': disable_keyword,
        }.get(x, default)

        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']

        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource_id='',
            package_id='',
            keyword=keyword,
            approval=None,
            admin_owner_orgs=None,
            org_name='',
            limit=limit,
            offset=offset,
            user_orgs='all',
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
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search_with_private_package_unauthorized(
        self,
        mock_args,
        mock_get_resource,
        mock_require_resource_package_access,
        mock_abort,
        mock_current_user_fixture,
        resource,
        mock_resource_object,
        app,
    ):
        """Test that accessing a private package's utilization calls abort(404)"""
        from werkzeug.exceptions import NotFound

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        # Mock require_resource_package_access to call abort(404)
        def require_resource_package_access_side_effect(resource_id, context):
            mock_abort(
                404,
                _(
                    'The requested URL was not found on the server. If you entered the'
                    ' URL manually please check your spelling and try again.'
                ),
            )

        mock_require_resource_package_access.side_effect = (
            require_resource_package_access_side_effect
        )

        # Mock abort to raise NotFound exception to stop execution
        mock_abort.side_effect = NotFound('Not Found')

        mock_args.get.side_effect = lambda x, default=None: {
            'resource_id': resource['id'],
            'package_id': '',
            'keyword': '',
            'disable_keyword': '',
            'organization': '',
        }.get(x, default)

        # Should raise NotFound due to abort(404)
        with pytest.raises(NotFound):
            UtilizationController.search()

        # Verify that abort(404) was called
        mock_abort.assert_called_once()
        assert mock_abort.call_args[0][0] == 404

    @patch(
        'ckanext.feedback.controllers.utilization.current_user',
        new_callable=lambda: str,
    )
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization.search_service'
        '.get_organization_name_from_pkg'
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.utilization.model.Package.get')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.request.args')
    def test_search_with_private_package_unauthorized_package_id(
        self,
        mock_args,
        mock_get_resource,
        mock_package_get,
        mock_get_org_name,
        mock_require_resource_package_access,
        mock_abort,
        mock_require_package_access,
        app,
    ):
        """Test accessing private package utilization calls abort(404)
        when using package_id"""
        from werkzeug.exceptions import NotFound

        # Mock get_resource to return None (so it tries package_id path)
        mock_get_resource.return_value = None

        # Mock Package.get to return a mock package
        mock_package = MagicMock()
        mock_package.id = 'test_package_id'
        mock_package.owner_org = 'test_org_id'
        mock_package_get.return_value = mock_package

        # Mock get_organization_name_from_pkg
        mock_get_org_name.return_value = 'test_organization'

        # Mock require_package_access to call abort(404)
        def require_package_access_side_effect(package_id, context):
            mock_abort(
                404,
                _(
                    'The requested URL was not found on the server. If you entered the'
                    ' URL manually please check your spelling and try again.'
                ),
            )

        mock_require_package_access.side_effect = require_package_access_side_effect

        # Mock abort to raise NotFound exception to stop execution
        mock_abort.side_effect = NotFound('Not Found')

        mock_args.get.side_effect = lambda x, default=None: {
            'resource_id': '',
            'package_id': 'test_package_id',
            'keyword': '',
            'disable_keyword': '',
            'organization': '',
        }.get(x, default)

        # Should raise NotFound due to abort(404)
        with pytest.raises(NotFound):
            UtilizationController.search()

        # Verify that abort(404) was called
        mock_abort.assert_called_once()
        assert mock_abort.call_args[0][0] == 404

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
        keyword = 'keyword'
        disable_keyword = 'disable keyword'
        page = 1
        limit = 20
        offset = 0
        pager_url = 'utilization.search'

        mock_pagination.return_value = [page, limit, offset, pager_url]
        mock_args.get.side_effect = lambda x, default: {
            'resource_id': '',
            'package_id': '',
            'keyword': keyword,
            'disable_keyword': disable_keyword,
            'organization': '',
        }.get(x, default)
        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']
        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.request', new_callable=MagicMock)
    @patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    def test_search_with_resource_id_not_found(
        self,
        mock_get_resource,
        mock_require_resource_package_access,
        mock_args,
        mock_pagination,
        mock_get_utilizations,
        mock_render,
        mock_page,
        admin_context,
    ):
        # Test case: resource_id is specified but get_resource returns None
        mock_get_resource.return_value = None

        keyword = 'keyword'
        disable_keyword = 'disable keyword'
        page = 1
        limit = 20
        offset = 0
        pager_url = 'utilization.search'

        mock_pagination.return_value = [page, limit, offset, pager_url]
        mock_args.args.get.side_effect = lambda x, default: {
            'resource_id': 'non_existent_resource_id',
            'package_id': '',
            'keyword': keyword,
            'disable_keyword': disable_keyword,
            'organization': '',
            'waiting': 'on',
            'approval': 'on',
        }.get(x, default)
        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']
        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        # require_resource_package_access is called even if resource is None
        mock_require_resource_package_access.assert_called_once()
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.request', new_callable=MagicMock)
    @patch('ckanext.feedback.controllers.utilization.model.Package.get')
    @patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    def test_search_with_package_id_not_found(
        self,
        mock_get_resource,
        mock_require_resource_package_access,
        mock_package_get,
        mock_args,
        mock_pagination,
        mock_get_utilizations,
        mock_render,
        mock_page,
        mock_require_package_access,
        admin_context,
    ):
        # Test case: package_id is specified but Package.get returns None
        mock_get_resource.return_value = None
        mock_package_get.return_value = None

        keyword = 'keyword'
        disable_keyword = 'disable keyword'
        page = 1
        limit = 20
        offset = 0
        pager_url = 'utilization.search'

        mock_pagination.return_value = [page, limit, offset, pager_url]
        mock_args.args.get.side_effect = lambda x, default: {
            'resource_id': '',
            'package_id': 'non_existent_package_id',
            'keyword': keyword,
            'disable_keyword': disable_keyword,
            'organization': '',
            'waiting': 'on',
            'approval': 'on',
        }.get(x, default)
        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']
        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        # Should call require_package_access even if package is None
        mock_require_package_access.assert_called_once()
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.request', new_callable=MagicMock)
    @patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    def test_search_with_resource_id_not_found_org_name_branch(
        self,
        mock_get_resource,
        mock_require_resource_package_access,
        mock_args,
        mock_pagination,
        mock_get_utilizations,
        mock_render,
        mock_page,
        admin_context,
    ):
        # Test case: resource_id is specified but get_resource returns None
        mock_get_resource.return_value = None

        keyword = 'keyword'
        disable_keyword = 'disable keyword'
        page = 1
        limit = 20
        offset = 0
        pager_url = 'utilization.search'

        mock_pagination.return_value = [page, limit, offset, pager_url]
        mock_args.args.get.side_effect = lambda x, default: {
            'resource_id': 'non_existent_resource_id',
            'package_id': '',
            'keyword': keyword,
            'disable_keyword': disable_keyword,
            'organization': '',  # Empty org_name to trigger the org_name logic
            'waiting': 'on',
            'approval': 'on',
        }.get(x, default)
        mock_get_utilizations.return_value = ['mock_utilizations', 'mock_total_count']
        mock_page.return_value = 'mock_page'

        UtilizationController.search()

        # Should render successfully even when resource_for_org is None
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_details_with_utilization_not_found(
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
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    def test_new(
        self,
        mock_get_authorized_package,
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
        mock_get_authorized_package.return_value = mock_package

        mock_dataset = MagicMock()
        mock_dataset.id = dataset['id']
        mock_dataset.owner_org = organization['id']
        mock_resource = mock_resource_object(
            org_id=organization['id'], org_name=organization['name']
        )
        mock_get_resource.return_value = mock_resource

        UtilizationController.new()

        mock_get_authorized_package.assert_called_once()

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
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    def test_new_with_resource_id(
        self,
        mock_get_authorized_package,
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
        mock_get_authorized_package.return_value = mock_package
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
        mock_get_authorized_package.assert_called_once()

        mock_render.assert_called_once_with(
            'utilization/new.html',
            {
                'pkg_dict': mock_package,
                'return_to_resource': False,
                'resource': mock_resource.Resource,
            },
        )
        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    def test_new_with_private_package_unauthorized(
        self,
        mock_get_resource,
        mock_get_authorized_package,
        mock_abort,
        resource,
        mock_resource_object,
    ):
        """Test accessing new utilization form for private package
        calls abort(404)"""
        from werkzeug.exceptions import NotFound

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        # Mock get_authorized_package to call abort(404)
        def get_authorized_package_side_effect(package_id, context):
            mock_abort(404, _(
                'The requested URL was not found on the server. If you entered the'
                ' URL manually please check your spelling and try again.'
            ))

        mock_get_authorized_package.side_effect = get_authorized_package_side_effect

        # Mock abort to raise NotFound exception to stop execution
        mock_abort.side_effect = NotFound('Not Found')

        # Should raise NotFound due to abort(404)
        with pytest.raises(NotFound):
            UtilizationController.new(resource_id=resource['id'])

        # Verify that abort(404) was called
        mock_abort.assert_called_once()
        assert mock_abort.call_args[0][0] == 404

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

    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.registration_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_create_with_database_error(
        self,
        mock_redirect_to,
        mock_flash_error,
        mock_session_commit,
        mock_summary_service,
        mock_registration_service,
        mock_form,
        mock_session_rollback,
        mock_is_recaptcha_verified,
    ):
        from sqlalchemy.exc import SQLAlchemyError

        package_name = 'test_package'
        resource_id = 'test_resource_id'
        title = 'Test Title'
        url = 'https://example.com'
        description = 'Test Description'

        mock_form.get.side_effect = lambda key, default='': {
            'package_name': package_name,
            'resource_id': resource_id,
            'title': title,
            'url': url,
            'description': description,
            'return_to_resource': False,
        }.get(key, default)

        mock_is_recaptcha_verified.return_value = True
        mock_session_commit.side_effect = SQLAlchemyError('Database error')

        UtilizationController.create()

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.new',
            resource_id=resource_id,
            title=title,
            description=description,
        )
        mock_session_rollback.assert_called_once()

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
        user_context,
        user,
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
    @patch(
        'ckanext.feedback.controllers.utilization.comment_service.get_resource',
        side_effect=Exception('boom'),
    )
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=True,
    )
    @patch('ckanext.feedback.controllers.utilization.registration_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    def test_create_admin_bypass_exception_then_proceed(
        self,
        mock_flash,
        mock_redirect_to,
        mock_commit,
        mock_summary,
        mock_registration,
        _mock_is_recaptcha,
        _mock_get_resource,
        mock_form,
        admin_context,
        sysadmin,
    ):
        mock_form.get.side_effect = ['pkg', 'rid', 't', 'https://e', 'd', True]
        UtilizationController.create()
        mock_registration.create_utilization.assert_called_once()
        mock_summary.create_utilization_summary.assert_called_once_with('rid')
        mock_commit.assert_called_once()
        mock_flash.assert_called_once()
        mock_redirect_to.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch(
        'ckanext.feedback.controllers.utilization.request.files.get', return_value=None
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        side_effect=Exception('boom'),
    )
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=True,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment'
    )
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_create_comment_admin_bypass_exception_then_proceed(
        self,
        mock_redirect,
        mock_flash,
        mock_commit,
        mock_create,
        _mock_is_recaptcha,
        _mock_get_utilization,
        _mock_files,
        mock_form,
        admin_context,
        sysadmin,
    ):
        mock_form.get.side_effect = [
            UtilizationCommentCategory.REQUEST.name,
            'ok',
            None,
        ]
        UtilizationController.create_comment(TEST_UTILIZATION_ID)
        mock_create.assert_called_once_with(
            TEST_UTILIZATION_ID, UtilizationCommentCategory.REQUEST.name, 'ok', None
        )
        mock_commit.assert_called_once()
        mock_flash.assert_called_once()
        mock_redirect.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=[None, None],
    )
    def test_reply_missing_fields_aborts_400(self, _gf, mock_abort):
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.utilization.has_organization_admin_role',
        return_value=False,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'content'],
    )
    def test_reply_restricted_non_admin(
        self, _gf, _has_org, MockCfg, _get_uti, mock_redirect, mock_flash, user_context
    ):
        cfg = MagicMock()
        cfg.utilization_comment.reply_open.is_enable.return_value = False
        cfg.recaptcha.force_all.get.return_value = False
        MockCfg.return_value = cfg
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_flash.assert_called_once()
        mock_redirect.assert_called_once()

    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'content'],
    )
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._upload_image',
        return_value='f.png',
    )
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=True,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment_reply'
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_reply_sysadmin_with_image_success(
        self,
        mock_redirect,
        mock_commit,
        mock_create,
        _get_uti,
        _recap,
        _upload,
        mock_files,
        _gf,
        admin_context,
        sysadmin,
    ):
        mock_files.return_value = MagicMock()
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_create.assert_called_once_with('cid', 'content', sysadmin['id'], 'f.png')
        mock_commit.assert_called_once()
        mock_redirect.assert_called_once()

    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'content'],
    )
    @patch(
        'ckanext.feedback.controllers.utilization.request.files.get',
        return_value=MagicMock(),
    )
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._upload_image',
        side_effect=toolkit.ValidationError({'upload': ['invalid']}),
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    def test_reply_image_validation_error(
        self, _get_uti, mock_redirect, mock_flash, *_
    ):
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_flash.assert_called_once()
        mock_redirect.assert_called_once()

    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'content'],
    )
    @patch(
        'ckanext.feedback.controllers.utilization.request.files.get',
        return_value=MagicMock(),
    )
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._upload_image',
        side_effect=Exception('boom'),
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment_reply'
    )
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch(
        'ckanext.feedback.controllers.utilization.has_organization_admin_role',
        return_value=True,
    )
    def test_reply_image_exception(
        self, _has_org, _get_uti, mock_commit, mock_create, mock_abort, *_
    ):
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_abort.assert_called_once_with(500)
        mock_create.assert_not_called()
        mock_commit.assert_not_called()

    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'content'],
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=False,
    )
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment_reply'
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch(
        'ckanext.feedback.controllers.utilization.has_organization_admin_role',
        return_value=False,
    )
    def test_reply_bad_recaptcha_flashes_error(
        self,
        _has_org,
        mock_commit,
        mock_create,
        mock_redirect,
        mock_flash,
        _recap,
        MockCfg,
        _get_uti,
        _gf,
        user_context,
        user,
    ):
        cfg = MagicMock()
        cfg.utilization_comment.reply_open.is_enable.return_value = True
        cfg.recaptcha.force_all.get.return_value = False
        MockCfg.return_value = cfg
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_flash.assert_called_once()
        mock_redirect.assert_called_once()
        mock_create.assert_not_called()
        mock_commit.assert_not_called()

    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'x' * 1001],
    )
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=True,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_reply_validation_error_flashes_error(self, mock_redirect, mock_flash, *_):
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_flash.assert_called_once()
        mock_redirect.assert_called_once()

    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'content'],
    )
    @patch(
        'ckanext.feedback.controllers.utilization.request.files.get', return_value=None
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch(
        'ckanext.feedback.controllers.utilization.has_organization_admin_role',
        return_value=True,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment_reply'
    )
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_reply_is_org_admin_path(self, mock_redirect, mock_commit, mock_create, *_):
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_create.assert_called_once()
        mock_commit.assert_called_once()
        mock_redirect.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment_reply'
    )
    @patch(
        'ckanext.feedback.controllers.utilization.validate_service.validate_comment',
        return_value=None,
    )
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch(
        'ckanext.feedback.controllers.utilization.request.files.get',
        return_value=None,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.has_organization_admin_role',
        return_value=False,
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=True,
    )
    def test_reply_with_error(
        self,
        _mock_recaptcha,
        MockFeedbackConfig,
        mock_get_utilization,
        _mock_has_org_admin,
        _mock_files_get,
        mock_form,
        _mock_validate,
        mock_create_reply,
        mock_commit,
        mock_rollback,
        mock_flash_error,
        mock_redirect,
        _mock_current_user,
        admin_context,
        sysadmin,
        utilization,
    ):
        """Test reply() error handling"""
        mock_form.get.side_effect = lambda k, d='': {
            'utilization_comment_id': 'comment-id',
            'reply_content': 'Reply',
        }.get(k, d)

        mock_uti = MagicMock(owner_org='org')
        mock_get_utilization.return_value = mock_uti

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.utilization_comment.reply_open.is_enable.return_value = True
        MockFeedbackConfig.return_value = cfg

        mock_commit.side_effect = Exception('Database error')

        UtilizationController.reply(utilization.id)

        mock_rollback.assert_called_once()
        mock_flash_error.assert_called_once()
        mock_redirect.assert_called_once()

    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch('ckanext.feedback.controllers.utilization._session')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.get_attached_image_path',
        return_value='p',
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.utilization.os.path.exists', return_value=True)
    @patch('ckanext.feedback.controllers.utilization.send_file', return_value='resp')
    def test_reply_attached_image_ok(
        self, mock_send_file, _exists, _get_path, mock_session, _get_uti
    ):
        reply_obj = MagicMock()
        reply_obj.attached_image_filename = 'f.png'
        mock_q = MagicMock()
        mock_q.join.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = reply_obj
        mock_session.query.return_value = mock_q
        resp = UtilizationController.reply_attached_image('uid', 'rid', 'f.png')
        assert resp == 'resp'
        mock_send_file.assert_called_once_with('p')

    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch('ckanext.feedback.controllers.utilization._session')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    def test_reply_attached_image_not_found(self, mock_abort, mock_session, _get_uti):
        mock_q = MagicMock()
        mock_q.join.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = None
        mock_session.query.return_value = mock_q
        UtilizationController.reply_attached_image('uid', 'rid', 'f.png')
        mock_abort.assert_called_once_with(404)

    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization'
        '.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch('ckanext.feedback.controllers.utilization._session')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization'
        '.detail_service.get_attached_image_path',
        return_value='p',
    )
    # fmt: on
    @patch(
        'ckanext.feedback.controllers.utilization.os.path.exists', return_value=False
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    def test_reply_attached_image_file_missing(
        self, mock_send_file, mock_abort, _exists, _get_path, mock_session, _get_uti
    ):
        reply_obj = MagicMock()
        reply_obj.attached_image_filename = 'f.png'
        mock_q = MagicMock()
        mock_q.join.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = reply_obj
        mock_session.query.return_value = mock_q
        UtilizationController.reply_attached_image('uid', 'rid', 'f.png')
        mock_abort.assert_called_once_with(404)
        mock_send_file.assert_not_called()

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

    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
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
        mock_get_authorized_package,
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
        mock_utilization.package_id = 'mock_package_id'
        mock_utilization.resource_id = 'mock_resource_id'
        mock_utilization.owner_org = 'mock_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_get_authorized_package.return_value = {'id': 'mock_package'}
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

    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
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
        mock_get_authorized_package,
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
        mock_utilization.package_id = 'mock_package_id'
        mock_utilization.resource_id = 'mock_resource_id'
        mock_utilization.owner_org = 'mock_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_get_authorized_package.return_value = {'id': 'mock_package'}
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

    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
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
        mock_get_authorized_package,
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
        mock_utilization.package_id = 'mock_package_id'
        mock_utilization.resource_id = 'mock_resource_id'
        mock_utilization.owner_org = 'mock_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_get_authorized_package.return_value = {'id': 'mock_package'}
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

    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
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
        mock_get_authorized_package,
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
        mock_utilization.package_id = 'mock_package_id'
        mock_utilization.owner_org = 'organization id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_get_authorized_package.return_value = {'id': 'mock_package'}
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
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    def test_details_thank_with_user(
        self,
        mock_get_authorized_package,
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
        mock_get_authorized_package.return_value = {'id': 'mock_package'}
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

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_details_with_private_package_unauthorized(
        self,
        mock_detail_service,
        mock_get_authorized_package,
        mock_abort,
    ):
        """Test that accessing details for private package calls abort(404)"""
        from werkzeug.exceptions import NotFound

        utilization_id = 'utilization_id'
        mock_utilization = MagicMock()
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization

        # Mock get_authorized_package to call abort(404)
        def get_authorized_package_side_effect(package_id, context):
            mock_abort(404, _(
                'The requested URL was not found on the server. If you entered the'
                ' URL manually please check your spelling and try again.'
            ))

        mock_get_authorized_package.side_effect = get_authorized_package_side_effect

        # Mock abort to raise NotFound exception to stop execution
        mock_abort.side_effect = NotFound('Not Found')

        # Should raise NotFound due to abort(404)
        with pytest.raises(NotFound):
            UtilizationController.details(utilization_id)

        # Verify that abort(404) was called
        mock_abort.assert_called_once()
        assert mock_abort.call_args[0][0] == 404

    @patch('ckanext.feedback.controllers.utilization.request.method', 'POST')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.validate_service')
    def test_check_comment_with_private_package_unauthorized(
        self,
        mock_validate_service,
        mock_detail_service,
        mock_get_resource,
        mock_get_authorized_package,
        mock_abort,
        mock_is_recaptcha_verified,
        mock_files_get,
        mock_form,
    ):
        """Test that check_comment for private package calls abort(404)"""
        from werkzeug.exceptions import NotFound

        utilization_id = 'utilization_id'
        mock_utilization = MagicMock()
        mock_utilization.package_id = 'mock_package_id'
        mock_utilization.resource_id = 'resource_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_detail_service.get_utilization_comment_categories.return_value = []

        # Mock form data
        mock_form.get.side_effect = lambda x, default=None: {
            'category': 'COMMENT',
            'comment-content': 'test content',
            'attached_image_filename': None,
        }.get(x, default)

        # Mock no attached image
        mock_files_get.return_value = None

        # Mock recaptcha verified
        mock_is_recaptcha_verified.return_value = True

        # Mock validate_comment to return None (no error)
        mock_validate_service.validate_comment.return_value = None

        # Mock resource
        mock_resource = MagicMock()
        mock_resource.Resource = MagicMock()
        mock_resource.Resource.package_id = 'package_id'
        mock_get_resource.return_value = mock_resource

        # Mock get_authorized_package to call abort(404)
        def get_authorized_package_side_effect(package_id, context):
            mock_abort(404, _(
                'The requested URL was not found on the server. If you entered the'
                ' URL manually please check your spelling and try again.'
            ))

        mock_get_authorized_package.side_effect = get_authorized_package_side_effect

        # Mock abort to raise NotFound exception to stop execution
        mock_abort.side_effect = NotFound('Not Found')

        # Should raise NotFound due to abort(404)
        with pytest.raises(NotFound):
            UtilizationController.check_comment(utilization_id)

        # Verify that abort(404) was called
        mock_abort.assert_called_once()
        assert mock_abort.call_args[0][0] == 404

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_approve(
        self,
        mock_redirect_to,
        mock_session_commit,
        mock_summary_service,
        mock_require_package_access,
        mock_detail_service,
        sysadmin,
        admin_context,
    ):
        utilization_id = 'utilization id'
        resource_id = 'resource id'

        mock_utilization = MagicMock()
        mock_utilization.package_id = 'mock_package_id'
        mock_utilization.resource_id = resource_id
        mock_detail_service.get_utilization.return_value = mock_utilization

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

    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    def test_approve_with_database_error(
        self,
        mock_flash_error,
        mock_redirect_to,
        mock_session_commit,
        mock_summary_service,
        mock_require_package_access,
        mock_detail_service,
        mock_session_rollback,
        sysadmin,
        mock_current_user_fixture,
        admin_context,
    ):
        from sqlalchemy.exc import SQLAlchemyError

        utilization_id = 'utilization id'
        mock_utilization = MagicMock()
        mock_utilization.package_id = 'mock_package_id'
        mock_utilization.resource_id = 'resource_id'
        mock_utilization.owner_org = 'org_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        # Simulate database error
        mock_session_commit.side_effect = SQLAlchemyError('Database error')

        UtilizationController.approve(utilization_id)

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_session_rollback.assert_called_once()

    @patch(
        'ckanext.feedback.controllers.utilization.'
        'UtilizationController._check_organization_admin_role'
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_approve_with_private_package_unauthorized(
        self,
        mock_detail_service,
        mock_require_package_access,
        mock_abort,
        mock_check_org_admin,
        admin_context,
    ):
        """Test that approving utilization for private package calls abort(404)"""
        from werkzeug.exceptions import NotFound

        utilization_id = 'utilization_id'
        mock_utilization = MagicMock()
        mock_utilization.package_id = 'mock_package_id'
        mock_utilization.resource_id = 'mock_resource_id'
        mock_detail_service.get_utilization.return_value = mock_utilization

        # Mock _check_organization_admin_role to pass (so we reach line 362-363)
        mock_check_org_admin.return_value = None

        # Mock require_package_access to call abort(404)
        def require_package_access_side_effect(package_id, context):
            mock_abort(404, _(
                'The requested URL was not found on the server. If you entered the'
                ' URL manually please check your spelling and try again.'
            ))

        mock_require_package_access.side_effect = require_package_access_side_effect

        # Mock abort to raise NotFound exception to stop execution
        mock_abort.side_effect = NotFound('Not Found')

        # Should raise NotFound due to abort(404)
        with pytest.raises(NotFound):
            UtilizationController.approve(utilization_id)

        # Verify that abort(404) was called
        mock_abort.assert_called_once()
        assert mock_abort.call_args[0][0] == 404

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

    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_create_comment_with_database_error(
        self,
        mock_detail_service,
        mock_session_commit,
        mock_flash_error,
        mock_redirect_to,
        mock_files_get,
        mock_form,
        mock_recaptcha,
        mock_session_rollback,
    ):
        from sqlalchemy.exc import SQLAlchemyError

        utilization_id = 'utilization id'

        mock_form.get.side_effect = lambda key, default='': {
            'category': 'REQUEST',
            'comment-content': 'Test comment',
            'attached_image_filename': None,
        }.get(key, default)
        mock_files_get.return_value = None
        mock_recaptcha.return_value = True

        mock_session_commit.side_effect = SQLAlchemyError('Database error')

        UtilizationController.create_comment(utilization_id)

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_session_rollback.assert_called_once()

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
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    def test_create_comment_with_ioerror_exception(
        self,
        mock_abort,
        mock_upload_image,
        mock_files,
        mock_form,
    ):
        """Test create_comment with IOError during image upload"""
        utilization_id = 'utilization id'
        category = 'category'
        content = 'content'
        attached_image_filename = 'attached_image_filename'

        mock_form.get.side_effect = [category, content, attached_image_filename]

        mock_file = MagicMock()
        mock_file.filename = attached_image_filename
        mock_file.content_type = 'image/png'
        mock_files.return_value = mock_file

        mock_upload_image.side_effect = IOError('Disk full')
        mock_abort.side_effect = Exception('Abort called')

        with pytest.raises(Exception):
            UtilizationController.create_comment(utilization_id)

        mock_upload_image.assert_called_once_with(mock_file)
        mock_abort.assert_called_once_with(500)

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._upload_image'
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    def test_create_comment_with_bad_image_exception(
        self,
        mock_abort,
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
        mock_abort.side_effect = Exception('Abort called')

        with pytest.raises(Exception):
            UtilizationController.create_comment(utilization_id)

        mock_upload_image.assert_called_once_with(mock_file)
        mock_abort.assert_called_once_with(500)

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
        user_context,
        user,
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
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_check_comment_POST_moral_keeper_ai_disable(
        self,
        mock_render,
        mock_get_authorized_package,
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

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_get_authorized_package.return_value = mock_package

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
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    def test_check_comment_with_ioerror_exception(
        self,
        mock_abort,
        mock_upload_image,
        mock_files,
        mock_form,
        mock_method,
    ):
        """Test check_comment with IOError during image upload"""
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
        mock_files.return_value = mock_file

        mock_upload_image.side_effect = OSError('Permission denied')
        mock_abort.side_effect = Exception('Abort called')

        with pytest.raises(Exception):
            UtilizationController.check_comment(utilization_id)

        mock_upload_image.assert_called_once_with(mock_file)
        mock_abort.assert_called_once_with(500)

    @patch('ckanext.feedback.controllers.utilization.request.method')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._upload_image'
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    def test_check_comment_with_bad_image_exception(
        self,
        mock_abort,
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
        mock_abort.side_effect = Exception('Abort called')

        with pytest.raises(Exception):
            UtilizationController.check_comment(utilization_id)

        mock_upload_image.assert_called_once_with(mock_file)
        mock_abort.assert_called_once_with(500)

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
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.create_utilization_comment_moral_check_log'
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_check_comment_POST_judgement_True(
        self,
        mock_render,
        mock_create_utilization_comment_moral_check_log,
        mock_get_authorized_package,
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

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_get_authorized_package.return_value = mock_package

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
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    def test_check_comment_POST_judgement_False(
        self,
        mock_get_authorized_package,
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

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_get_authorized_package.return_value = mock_package

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
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.create_utilization_comment_moral_check_log'
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    def test_check_comment_POST_suggested(
        self,
        mock_render,
        mock_create_utilization_comment_moral_check_log,
        mock_get_authorized_package,
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

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_get_utilization.return_value = mock_utilization
        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_get_authorized_package.return_value = mock_package

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
        user_context,
        user,
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
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_approve_comment(
        self,
        mock_require_package_access,
        mock_redirect_to,
        mock_session_commit,
        mock_detail_service,
        admin_context,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'

        mock_utilization = MagicMock()
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization

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

    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_approve_comment_with_database_error(
        self,
        mock_require_package_access,
        mock_flash_error,
        mock_detail_service,
        mock_session_commit,
        mock_redirect_to,
        mock_session_rollback,
        admin_context,
    ):
        from sqlalchemy.exc import SQLAlchemyError

        utilization_id = 'utilization id'
        comment_id = 'comment id'

        mock_utilization = MagicMock()
        mock_utilization.package_id = 'package_id'
        mock_utilization.owner_org = 'org_id'
        mock_detail_service.get_utilization.return_value = mock_utilization

        mock_session_commit.side_effect = SQLAlchemyError('Database error')

        UtilizationController.approve_comment(utilization_id, comment_id)

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_session_rollback.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_edit(
        self,
        mock_require_package_access,
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
        mock_require_package_access.return_value = {'id': 'mock_package'}

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

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_edit_with_private_package_unauthorized(
        self,
        mock_detail_service,
        mock_require_package_access,
        mock_abort,
        admin_context,
    ):
        """Test that editing utilization for private package calls abort(404)"""
        from werkzeug.exceptions import NotFound

        utilization_id = 'utilization_id'
        mock_utilization = MagicMock()
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization

        # Mock require_package_access to call abort(404)
        def require_package_access_side_effect(package_id, context):
            mock_abort(404, _(
                'The requested URL was not found on the server. If you entered the'
                ' URL manually please check your spelling and try again.'
            ))

        mock_require_package_access.side_effect = require_package_access_side_effect

        # Mock abort to raise NotFound exception to stop execution
        mock_abort.side_effect = NotFound('Not Found')

        # Should raise NotFound due to abort(404)
        with pytest.raises(NotFound):
            UtilizationController.edit(utilization_id)

        # Verify that abort(404) was called
        mock_abort.assert_called_once()
        assert mock_abort.call_args[0][0] == 404

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_update(
        self,
        mock_require_package_access,
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
        mock_require_package_access.return_value = {'id': 'mock_package'}
        UtilizationController.update(utilization_id)

        mock_edit_service.update_utilization.assert_called_once_with(
            utilization_id, title, url, description
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )

    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_update_with_database_error(
        self,
        mock_require_package_access,
        mock_detail_service,
        mock_redirect_to,
        mock_flash_error,
        mock_session_commit,
        mock_edit_service,
        mock_form,
        mock_session_rollback,
        admin_context,
    ):
        from sqlalchemy.exc import SQLAlchemyError

        utilization_id = 'utilization id'

        mock_utilization = MagicMock()
        mock_utilization.package_id = 'package_id'
        mock_utilization.owner_org = 'org_id'
        mock_detail_service.get_utilization.return_value = mock_utilization

        mock_form.get.side_effect = lambda key, default='': {
            'title': 'Test Title',
            'url': 'https://example.com',
            'description': 'Test Description',
        }.get(key, default)

        mock_session_commit.side_effect = SQLAlchemyError('Database error')

        UtilizationController.update(utilization_id)

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.edit', utilization_id=utilization_id
        )
        mock_session_rollback.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_success')
    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_update_without_title_description(
        self,
        mock_require_package_access,
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
        mock_require_package_access.return_value = {'id': 'mock_package'}
        UtilizationController.update(utilization_id)

        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_update_with_invalid_title_length(
        self,
        mock_require_package_access,
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
        mock_require_package_access.return_value = {'id': 'mock_package'}
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
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_update_without_url(
        self,
        mock_require_package_access,
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
        mock_require_package_access.return_value = {'id': 'mock_package'}
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
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_update_with_invalid_description_length(
        self,
        mock_require_package_access,
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
        mock_require_package_access.return_value = {'id': 'mock_package'}
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
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_delete(
        self,
        mock_require_package_access,
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
        assert mock_session_commit.call_count == 1
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once_with('utilization.search')

    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.edit_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_delete_with_database_error(
        self,
        mock_require_package_access,
        mock_redirect_to,
        mock_flash_error,
        mock_session_commit,
        mock_edit_service,
        mock_detail_service,
        mock_session_rollback,
        admin_context,
    ):
        from sqlalchemy.exc import SQLAlchemyError

        utilization_id = 'utilization id'

        utilization = MagicMock()
        utilization.resource_id = 'resource_id'
        utilization.package_id = 'package_id'
        utilization.owner_org = 'org_id'
        mock_detail_service.get_utilization.return_value = utilization

        mock_session_commit.side_effect = SQLAlchemyError('Database error')

        UtilizationController.delete(utilization_id)

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_session_rollback.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_create_issue_resolution(
        self,
        mock_require_package_access,
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

    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_create_issue_resolution_with_database_error(
        self,
        mock_require_package_access,
        mock_redirect_to,
        mock_flash_error,
        mock_session_commit,
        mock_detail_service,
        mock_form,
        mock_session_rollback,
        admin_context,
    ):
        from sqlalchemy.exc import SQLAlchemyError

        utilization_id = 'utilization id'

        mock_utilization = MagicMock()
        mock_utilization.package_id = 'package_id'
        mock_utilization.owner_org = 'org_id'
        mock_detail_service.get_utilization.return_value = mock_utilization

        mock_form.get.return_value = 'Test description'

        mock_session_commit.side_effect = SQLAlchemyError('Database error')

        UtilizationController.create_issue_resolution(utilization_id)

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_session_rollback.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.summary_service')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_create_issue_resolution_without_description(
        self,
        mock_require_package_access,
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
        mock_utilization.package_id = 'mock_package_id'
        mock_utilization.owner_org = 'test_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_require_package_access.return_value = {'id': 'mock_package'}

        mock_form.get.return_value = description
        mock_redirect_to.return_value = ''

        with admin_context.test_request_context():
            UtilizationController.create_issue_resolution(utilization_id)

        mock_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.os.path.exists')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_attached_image_with_sysadmin(
        self,
        mock_require_package_access,
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
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_attached_image_with_user(
        self,
        mock_require_package_access,
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
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_attached_image_with_not_found_attached_image(
        self,
        mock_require_package_access,
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
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_attached_image_with_not_found_comment(
        self,
        mock_require_package_access,
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
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch(
        'ckanext.feedback.controllers.utilization.current_user.sysadmin',
        return_value=True,
    )
    def test_check_organization_admin_role_with_sysadmin(
        self,
        mock_sysadmin,
        mocked_detail_service,
        mock_require_package_access,
        mock_toolkit_abort,
        admin_context,
    ):

        organization_id = 'organization id'

        mocked_utilization = MagicMock()
        mocked_utilization.owner_org = organization_id
        mocked_utilization.package_id = 'mock_package_id'
        mocked_detail_service.get_utilization.return_value = mocked_utilization

        with admin_context:
            UtilizationController._check_organization_admin_role('utilization_id')

        mock_require_package_access.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckan.model.Group.get')
    @patch('ckanext.feedback.controllers.utilization.has_organization_admin_role')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_check_organization_adimn_role_with_org_admin(
        self,
        mock_require_package_access,
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
        mock_require_package_access.return_value = {'id': 'mock_package'}

        mock_has_organization_admin_role.return_value = True

        with admin_context:
            UtilizationController._check_organization_admin_role('utilization_id')
        mock_toolkit_abort.assert_not_called()
        mock_has_organization_admin_role.assert_called_once_with(organization_id)

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckan.model.Group.get')
    @patch('ckanext.feedback.controllers.utilization.has_organization_admin_role')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_check_organization_adimn_role_with_user(
        self,
        mock_require_package_access,
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
        mock_require_package_access.return_value = {'id': 'mock_package'}

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
    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image(
        self,
        mock_get_uploader,
        mock_get_upload_destination,
    ):
        mock_image = MagicMock()
        mock_image.filename = 'test.png'
        mock_image.content_type = 'image/png'

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

    def test_upload_image_with_invalid_extension(self):
        """Test _upload_image with invalid file extension"""
        mock_image = MagicMock()
        mock_image.filename = 'test.txt'
        mock_image.content_type = 'text/plain'

        with pytest.raises(toolkit.ValidationError) as exc_info:
            UtilizationController._upload_image(mock_image)

        assert 'Image Upload' in str(exc_info.value)
        assert 'Invalid file extension' in str(exc_info.value)

    def test_upload_image_with_invalid_mimetype(self):
        """Test _upload_image with invalid mimetype"""
        mock_image = MagicMock()
        mock_image.filename = 'test.png'
        mock_image.content_type = 'application/pdf'

        with pytest.raises(toolkit.ValidationError) as exc_info:
            UtilizationController._upload_image(mock_image)

        assert 'Image Upload' in str(exc_info.value)
        assert 'Invalid file type' in str(exc_info.value)

    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_upload_destination'
    )
    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_without_content_type(
        self,
        mock_get_uploader,
        mock_get_upload_destination,
    ):
        """Test _upload_image without content_type (should pass validation)"""
        mock_image = MagicMock()
        mock_image.filename = 'test.jpg'
        mock_image.content_type = None

        mock_get_upload_destination.return_value = '/test/upload/path'

        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = 'test_image.jpg'

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        result = UtilizationController._upload_image(mock_image)

        assert result == 'test_image.jpg'
        mock_get_upload_destination.assert_called_once()
        mock_get_uploader.assert_called_once_with('/test/upload/path')
        mock_uploader.upload.assert_called_once()

    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_upload_destination'
    )
    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_without_filename(
        self,
        mock_get_uploader,
        mock_get_upload_destination,
    ):
        """Test _upload_image without filename (should skip extension validation)"""
        mock_image = MagicMock()
        mock_image.filename = None
        mock_image.content_type = 'image/png'

        mock_get_upload_destination.return_value = '/test/upload/path'

        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = 'generated_filename.png'

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        result = UtilizationController._upload_image(mock_image)

        assert result == 'generated_filename.png'
        mock_get_upload_destination.assert_called_once()
        mock_get_uploader.assert_called_once_with('/test/upload/path')
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
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    def test_details_without_user(
        self,
        mock_get_authorized_package,
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
        mock_get_authorized_package.return_value = {'id': 'mock_package'}
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
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    def test_check_comment_POST_ai_disabled(
        self,
        mock_get_authorized_package,
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
        utilization_id = 'resource_id'
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

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_get_authorized_package.return_value = mock_package

        mock_get_utilization_comment_categories.return_value = 'mock_categories'

        UtilizationController.check_comment(utilization_id)

        mock_check_ai_comment.assert_not_called()

        mock_render.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.os.path.exists')
    @patch('ckanext.feedback.controllers.utilization.send_file')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_attached_image_file_not_found(
        self,
        mock_require_package_access,
        mock_send_file,
        mock_exists,
        mock_detail_service,
    ):
        utilization_id = 'utilization id'
        comment_id = 'comment id'
        attached_image_filename = 'attached_image_filename'

        mock_utilization = MagicMock()
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_detail_service.get_utilization_comment.return_value = 'mock_comment'
        mock_detail_service.get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = False

        mock_require_package_access.return_value = None

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
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_attached_image_with_current_user_not_model_user(
        self,
        mock_require_package_access,
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
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_attached_image_with_org_admin(
        self,
        mock_require_package_access,
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
        mock_utilization.package_id = 'mock_package_id'
        mock_utilization.owner_org = 'test_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_require_package_access.return_value = {'id': 'mock_package'}
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
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    def test_attached_image_with_normal_user(
        self,
        mock_require_package_access,
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
        mock_utilization.package_id = 'mock_package_id'
        mock_utilization.owner_org = 'test_org_id'
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_require_package_access.return_value = {'id': 'mock_package'}
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
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    def test_check_comment_POST_ai_check_false(
        self,
        mock_get_authorized_package,
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
        utilization_id = 'resource_id'
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

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_get_utilization.return_value = mock_utilization

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_get_resource.return_value = mock_resource

        # Mock get_authorized_package to return package data
        mock_get_authorized_package.return_value = {'id': 'mock_package'}

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

    @patch('ckanext.feedback.controllers.utilization.validate_service.validate_comment')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('flask_login.utils._get_user')
    def test_process_comment_input_admin_bypass_exception_fallback(
        self, mock_current_user, mock_files, mock_form,
        mock_config, mock_get_utilization,
        mock_recaptcha, mock_validate, sysadmin
    ):
        """Test _process_comment_input with exception in get_utilization
        fallback to sysadmin bypass"""
        mock_current_user.return_value = model.User.get(sysadmin['id'])

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        mock_config.return_value = cfg

        mock_get_utilization.side_effect = Exception('Utilization not found')

        mock_recaptcha.return_value = False
        mock_validate.return_value = None

        mock_files.return_value = None
        mock_form.get.side_effect = ['REQUEST', 'test content', None]

        result = UtilizationController._process_comment_input(
            'image-upload', 'utilization-id'
        )

        assert result.error_response is None
        assert result.form_data['category'] == 'REQUEST'

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
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.create_utilization_comment_moral_check_log'
    )
    def test_check_comment_post_ai_check_true(
        self,
        mock_create_utilization_comment_moral_check_log,
        mock_get_authorized_package,
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
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_get_authorized_package.return_value = mock_package

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

    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    @patch(
        'ckanext.feedback.services.common.config.BaseConfig.is_enable',
        return_value=True,
    )
    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.request.method', 'POST')
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.validate_service')
    @patch('ckanext.feedback.controllers.utilization.check_ai_comment')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_check_comment_with_moral_check_log_database_error(
        self,
        mock_redirect_to,
        mock_flash_error,
        mock_session_commit,
        mock_get_authorized_package,
        mock_get_resource,
        mock_detail_service,
        mock_check_ai_comment,
        mock_validate_service,
        mock_is_recaptcha_verified,
        mock_files_get,
        mock_form,
        mock_session_rollback,
        mock_is_enable,
        mock_FeedbackConfig,
        mock_utilization_object,
        mock_resource_object,
    ):
        from sqlalchemy.exc import SQLAlchemyError

        utilization_id = 'test_utilization_id'

        mock_form.get.side_effect = lambda x, default=None: {
            'category': 'REQUEST',
            'comment-content': 'Test comment content',
            'attached_image_filename': None,
            'comment-suggested': 'True',
            'action': 'confirm',
            'input-comment': 'Original comment',
            'suggested-comment': 'Suggested comment',
        }.get(x, default)

        mock_files_get.return_value = None

        mock_is_recaptcha_verified.return_value = True

        mock_validate_service.validate_comment.return_value = None

        mock_utilization = mock_utilization_object(
            resource_id='mock_resource_id', owner_org='mock_org_id'
        )
        mock_detail_service.get_utilization.return_value = mock_utilization
        mock_detail_service.get_utilization_comment_categories.return_value = []

        mock_resource = mock_resource_object(
            org_id='mock_org_id', org_name='mock_organization_name'
        )
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_resource.Resource.package.owner_org = 'mock_org_id'
        mock_get_resource.return_value = mock_resource

        mock_get_authorized_package.return_value = {'id': 'package_id'}

        mock_moral_keeper_ai = MagicMock()
        mock_moral_keeper_ai.is_enable.return_value = True
        mock_FeedbackConfig.return_value.moral_keeper_ai = mock_moral_keeper_ai

        mock_session_commit.side_effect = SQLAlchemyError('Database error')

        UtilizationController.check_comment(utilization_id)

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_session_rollback.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=True,
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service.get_utilization')
    @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization'
        '.detail_service.get_utilization_comment_categories',
        return_value=['REQUEST'],
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
    def test_check_comment_admin_bypass_exception_then_render(
        self,
        mock_get_resource,
        mock_render,
        _cats,
        mock_get_authorized_package,
        mock_get_utilization,
        _recap,
        MockCfg,
        admin_context,
        sysadmin,
    ):
        """Test check_comment renders successfully with normal flow"""
        MockCfg.return_value.moral_keeper_ai.is_enable.return_value = False

        utilization_mock = MagicMock(owner_org='org', resource_id='rid')
        mock_get_utilization.return_value = utilization_mock

        mock_get_authorized_package.return_value = {
            'id': 'pkg-id',
            'name': 'test-package',
        }

        res = MagicMock()
        res.Resource = MagicMock()
        res.Resource.package_id = 'pkg-id'
        res.Resource.package.owner_org = 'org'
        res.organization_name = 'test-org'
        mock_get_resource.return_value = res

        with patch(
            'ckanext.feedback.controllers.utilization.request.method',
            return_value='POST',
        ), patch('ckanext.feedback.controllers.utilization.request.form.get') as gf:
            gf.side_effect = lambda k, default=None: {
                'category': 'REQUEST',
                'comment-content': 'ok',
                'attached_image_filename': None,
                'comment-suggested': False,
                'rating': '',
            }.get(k, default)

            UtilizationController.check_comment('uid')

        mock_render.assert_called_once_with(
            'utilization/comment_check.html',
            {
                'pkg_dict': {'id': 'pkg-id', 'name': 'test-package'},
                'utilization_id': 'uid',
                'utilization': utilization_mock,
                'content': 'ok',
                'selected_category': 'REQUEST',
                'categories': ['REQUEST'],
                'attached_image_filename': None,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=False,
    )
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.current_user', None)
    def test_create_non_user_bad_recaptcha(
        self, mock_redirect, mock_flash, _recap, mock_form
    ):
        mock_form.get.side_effect = ['pkg', 'rid', 't', 'https://e', 'd', True]
        UtilizationController.create()
        mock_flash.assert_called_once()
        mock_redirect.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.current_user', None)
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.UtilizationController.details')
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=False,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.request.files.get', return_value=None
    )
    @patch('ckanext.feedback.controllers.utilization.request.form')
    def test_create_comment_non_user_bad_recaptcha(
        self, mock_form, mock_files, mock_recap, mock_details, mock_flash
    ):
        mock_form.get.side_effect = ['REQUEST', 'content', None]
        UtilizationController.create_comment(TEST_UTILIZATION_ID)
        mock_flash.assert_called_once()
        mock_details.assert_called_once()

    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'content'],
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        side_effect=Exception('boom'),
    )
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_reply_utilization_not_found(
        self, mock_redirect, mock_flash, mock_get_utilization, mock_gf
    ):
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_flash.assert_called_once()
        mock_redirect.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.current_user', None)
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=False,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'content'],
    )
    def test_reply_non_user_bad_recaptcha(
        self, mock_gf, mock_get_utilization, mock_recap, mock_flash, mock_redirect
    ):
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_flash.assert_called_once()
        mock_redirect.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment_reply'
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=False,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.has_organization_admin_role',
        side_effect=Exception('boom'),
    )
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'content'],
    )
    def test_reply_admin_bypass_exception(
        self,
        mock_gf,
        mock_get_utilization,
        mock_has_org,
        mock_recap,
        mock_flash,
        mock_redirect,
        mock_create,
        mock_commit,
        user_context,
        user,
    ):
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_flash.assert_called_once()
        mock_redirect.assert_called_once()
        mock_create.assert_not_called()
        mock_commit.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment_reply'
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=False,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.has_organization_admin_role',
        return_value=False,
    )
    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'content'],
    )
    def test_reply_open_exception(
        self,
        mock_gf,
        mock_get_utilization,
        MockCfg,
        mock_has_org,
        mock_recap,
        mock_flash,
        mock_redirect,
        mock_create,
        mock_commit,
        user_context,
        user,
    ):
        cfg = MagicMock()
        cfg.utilization_comment.reply_open.is_enable.side_effect = Exception('boom')
        cfg.recaptcha.force_all.get.return_value = False
        MockCfg.return_value = cfg
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_flash.assert_called_once()
        mock_redirect.assert_called_once()
        mock_create.assert_not_called()
        mock_commit.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment_reply'
    )
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=False,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.has_organization_admin_role',
        side_effect=Exception('boom'),
    )
    @patch('ckanext.feedback.controllers.utilization.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch(
        'ckanext.feedback.controllers.utilization.request.form.get',
        side_effect=['cid', 'content'],
    )
    def test_reply_org_admin_check_exception(
        self,
        mock_gf,
        mock_get_utilization,
        MockCfg,
        mock_has_org,
        mock_recap,
        mock_flash,
        mock_redirect,
        mock_create,
        mock_commit,
        user_context,
        user,
    ):
        cfg = MagicMock()
        cfg.utilization_comment.reply_open.is_enable.return_value = False
        cfg.recaptcha.force_all.get.return_value = False
        MockCfg.return_value = cfg
        UtilizationController.reply(TEST_UTILIZATION_ID)
        mock_flash.assert_called_once()
        mock_redirect.assert_called_once()
        mock_create.assert_not_called()
        mock_commit.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.current_user', None)
    @patch('ckanext.feedback.controllers.utilization._session')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.utilization'
        '.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    # fmt: on
    def test_reply_attached_image_non_user(self, mock_get_utilization, mock_session):
        reply_obj = MagicMock()
        reply_obj.attached_image_filename = 'f.png'
        mock_q = MagicMock()
        mock_q.join.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = reply_obj
        mock_session.query.return_value = mock_q

        # fmt: off
        with patch(
            'ckanext.feedback.controllers.utilization'
            '.detail_service.get_attached_image_path',
            return_value='p',
        ), patch(
            'ckanext.feedback.controllers.utilization.os.path.exists', return_value=True
        ), patch(
            'ckanext.feedback.controllers.utilization.send_file', return_value='resp'
        ) as mock_send:
            resp = UtilizationController.reply_attached_image('uid', 'rid', 'f.png')
            assert resp == 'resp'
            mock_send.assert_called_once_with('p')
        # fmt: on

    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=MagicMock(owner_org='org'),
    )
    @patch('ckanext.feedback.controllers.utilization._session')
    def test_reply_attached_image_with_approval_filter(
        self, mock_session, mock_get_utilization, user_context, user
    ):
        reply_obj = MagicMock()
        reply_obj.attached_image_filename = 'f.png'
        mock_q = MagicMock()
        mock_q.join.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = reply_obj
        mock_session.query.return_value = mock_q
        # fmt: off
        with patch(
            'ckanext.feedback.controllers.utilization.detail_service'
            '.get_attached_image_path',
            return_value='p',
        ), patch(
            'ckanext.feedback.controllers.utilization.os.path.exists', return_value=True
        ), patch(
            'ckanext.feedback.controllers.utilization.send_file', return_value='resp'
        ) as mock_send:
            resp = UtilizationController.reply_attached_image('uid', 'rid', 'f.png')
            assert resp == 'resp'
            mock_send.assert_called_once_with('p')
        # fmt: on

    @patch('ckanext.feedback.controllers.utilization.current_user', None)
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.UtilizationController.details')
    @patch(
        'ckanext.feedback.controllers.utilization.is_recaptcha_verified',
        return_value=False,
    )
    @patch(
        'ckanext.feedback.controllers.utilization.request.files.get', return_value=None
    )
    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch(
        'ckanext.feedback.controllers.utilization.request.method', return_value='POST'
    )
    def test_check_comment_non_user_bad_recaptcha(
        self, mock_method, mock_form, mock_files, mock_recap, mock_details, mock_flash
    ):
        mock_form.get.side_effect = lambda x, default: {
            'category': 'REQUEST',
            'comment-content': 'content',
            'attached_image_filename': None,
        }.get(x, default)
        UtilizationController.check_comment(TEST_UTILIZATION_ID)
        mock_flash.assert_called_once()
        mock_details.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service.get_utilization',
        return_value=None,
    )
    def test_reply_attached_image_not_found_utilization(
        self, mock_get_utilization, mock_abort
    ):
        UtilizationController.reply_attached_image(
            TEST_UTILIZATION_ID, TEST_REPLY_ID, TEST_IMAGE_FILENAME
        )
        mock_get_utilization.assert_called_once_with(TEST_UTILIZATION_ID)
        mock_abort.assert_called_once_with(404)

    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._check_organization_admin_role'  # noqa: E501
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_approve_reply_value_error(
        self,
        mock_redirect,
        mock_commit,
        mock_detail_service,
        mock_check_org_role,
        admin_context,
        sysadmin,
    ):
        mock_check_org_role.return_value = None

        mock_detail_service.approve_utilization_comment_reply.side_effect = ValueError(
            'test error'
        )
        self._setup_mock_utilization(mock_detail_service)

        with patch('ckanext.feedback.controllers.utilization.log.warning') as mock_log:
            UtilizationController.approve_reply(TEST_UTILIZATION_ID, TEST_REPLY_ID)
            mock_log.assert_called_once()
            self._assert_approve_reply_common(
                mock_redirect, mock_commit, should_commit=False
            )

    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._check_organization_admin_role'  # noqa: E501
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_approve_reply_permission_error(
        self,
        mock_redirect,
        mock_flash,
        mock_commit,
        mock_detail_service,
        mock_check_org_role,
        admin_context,
        sysadmin,
    ):
        mock_check_org_role.return_value = None

        mock_detail_service.approve_utilization_comment_reply.side_effect = (
            PermissionError('test error')
        )
        self._setup_mock_utilization(mock_detail_service)

        UtilizationController.approve_reply(TEST_UTILIZATION_ID, TEST_REPLY_ID)
        mock_flash.assert_called_once()
        self._assert_approve_reply_common(
            mock_redirect, mock_commit, should_commit=False
        )

    @patch(
        'ckanext.feedback.controllers.utilization.UtilizationController._check_organization_admin_role'  # noqa: E501
    )
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_approve_reply_success(
        self,
        mock_redirect,
        mock_commit,
        mock_detail_service,
        mock_check_org_role,
        admin_context,
        sysadmin,
    ):
        self._setup_mock_utilization(mock_detail_service)
        mock_check_org_role.return_value = None

        UtilizationController.approve_reply(TEST_UTILIZATION_ID, TEST_REPLY_ID)
        mock_detail_service.approve_utilization_comment_reply.assert_called_once_with(
            TEST_REPLY_ID, sysadmin['id']
        )
        self._assert_approve_reply_common(
            mock_redirect, mock_commit, should_commit=True
        )


@pytest.mark.usefixtures('with_request_context')
@pytest.mark.db_test
class TestUtilizationCreatePreviousLog:
    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_resource_by_utilization_id'
    )
    @patch(
        'ckanext.feedback.controllers.'
        'utilization.detail_service'
        '.create_utilization_comment_moral_check_log'
    )
    def test_create_previous_log_moral_keeper_ai_disabled(
        self,
        mock_create_moral_check_log,
        mock_get_resource_by_utilization_id,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = False

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource_by_utilization_id.return_value = resource

        return_value = UtilizationController.create_previous_log(TEST_UTILIZATION_ID)

        mock_create_moral_check_log.assert_not_called()
        assert return_value == ('', 204)

    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_resource_by_utilization_id'
    )
    @patch('ckanext.feedback.controllers.utilization.request.get_json')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment_moral_check_log'
    )
    def test_create_previous_log_previous_type_suggestion(
        self,
        mock_create_moral_check_log,
        mock_session_commit,
        mock_get_json,
        mock_get_resource_by_utilization_id,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = True

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource_by_utilization_id.return_value = resource
        mock_get_json.return_value = {
            'previous_type': 'suggestion',
            'input_comment': 'test_input_comment',
            'suggested_comment': 'test_suggested_comment',
        }
        mock_create_moral_check_log.return_value = None

        return_value = UtilizationController.create_previous_log(TEST_UTILIZATION_ID)

        mock_create_moral_check_log.assert_called_once_with(
            utilization_id=TEST_UTILIZATION_ID,
            action=MoralCheckAction.PREVIOUS_SUGGESTION.name,
            input_comment='test_input_comment',
            suggested_comment='test_suggested_comment',
            output_comment=None,
        )
        mock_session_commit.assert_called_once()
        assert return_value == ('', 204)

    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_resource_by_utilization_id'
    )
    @patch('ckanext.feedback.controllers.utilization.request.get_json')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment_moral_check_log'
    )
    def test_create_previous_log_previous_type_confirm(
        self,
        mock_create_moral_check_log,
        mock_session_commit,
        mock_get_json,
        mock_get_resource_by_utilization_id,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = True

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource_by_utilization_id.return_value = resource
        mock_get_json.return_value = {
            'previous_type': 'confirm',
            'input_comment': 'test_input_comment',
            'suggested_comment': 'test_suggested_comment',
        }
        mock_create_moral_check_log.return_value = None

        return_value = UtilizationController.create_previous_log(TEST_UTILIZATION_ID)

        mock_create_moral_check_log.assert_called_once_with(
            utilization_id=TEST_UTILIZATION_ID,
            action=MoralCheckAction.PREVIOUS_CONFIRM.name,
            input_comment='test_input_comment',
            suggested_comment='test_suggested_comment',
            output_comment=None,
        )
        mock_session_commit.assert_called_once()
        assert return_value == ('', 204)

    @patch(
        'ckanext.feedback.controllers.utilization.'
        'detail_service.get_resource_by_utilization_id'
    )
    @patch('ckanext.feedback.controllers.utilization.request.get_json')
    @patch(
        'ckanext.feedback.controllers.utilization.detail_service'
        '.create_utilization_comment_moral_check_log'
    )
    def test_create_previous_log_previous_type_none(
        self,
        mock_create_moral_check_log,
        mock_get_json,
        mock_get_resource_by_utilization_id,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = True

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource_by_utilization_id.return_value = resource
        mock_get_json.return_value = {
            'previous_type': 'invalid_type',
            'input_comment': 'test_input_comment',
            'suggested_comment': 'test_suggested_comment',
        }

        return_value = UtilizationController.create_previous_log(TEST_UTILIZATION_ID)

        mock_create_moral_check_log.assert_not_called()
        assert return_value == ('', 204)

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_attached_image_with_private_package_unauthorized(
        self,
        mock_detail_service,
        mock_require_package_access,
        mock_abort,
    ):
        from werkzeug.exceptions import NotFound

        utilization_id = 'utilization_id'
        comment_id = 'comment_id'
        attached_image_filename = 'test.jpg'

        mock_utilization = MagicMock()
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization

        def require_package_access_side_effect(package_id, context):
            mock_abort(
                404,
                _(
                    'The requested URL was not found on the server. If you entered the'
                    ' URL manually please check your spelling and try again.'
                ),
            )

        mock_require_package_access.side_effect = require_package_access_side_effect

        mock_abort.side_effect = NotFound('Not Found')

        with pytest.raises(NotFound):
            UtilizationController.attached_image(
                utilization_id, comment_id, attached_image_filename
            )

        mock_abort.assert_called_once()
        assert mock_abort.call_args[0][0] == 404

    @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
    @patch('ckanext.feedback.controllers.utilization.require_package_access')
    @patch('ckanext.feedback.controllers.utilization.detail_service')
    def test_check_organization_admin_role_with_private_package_unauthorized(
        self,
        mock_detail_service,
        mock_require_package_access,
        mock_abort,
        admin_context,
    ):
        from werkzeug.exceptions import NotFound

        utilization_id = 'utilization_id'
        mock_utilization = MagicMock()
        mock_utilization.package_id = 'mock_package_id'
        mock_detail_service.get_utilization.return_value = mock_utilization

        def require_package_access_side_effect(package_id, context):
            mock_abort(
                404,
                _(
                    'The requested URL was not found on the server. If you entered the'
                    ' URL manually please check your spelling and try again.'
                ),
            )

        mock_require_package_access.side_effect = require_package_access_side_effect

        mock_abort.side_effect = NotFound('Not Found')

        with pytest.raises(NotFound):
            UtilizationController._check_organization_admin_role(utilization_id)

        mock_abort.assert_called_once()
        assert mock_abort.call_args[0][0] == 404

    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    def test_persist_operation_success(self, mock_commit, mock_rollback):
        """Test _persist_operation with successful operation"""
        utilization_id = 'test_id'
        error_message = 'Test error'

        operation_called = False

        def successful_operation():
            nonlocal operation_called
            operation_called = True

        result = UtilizationController._persist_operation(
            successful_operation, utilization_id, error_message
        )

        assert result.success is True
        assert result.error_message is None
        assert operation_called is True
        mock_commit.assert_called_once()
        mock_rollback.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.log.exception')
    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    def test_persist_operation_with_sqlalchemy_error(
        self, mock_commit, mock_rollback, mock_log
    ):
        """Test _persist_operation with SQLAlchemyError"""
        from sqlalchemy.exc import SQLAlchemyError

        utilization_id = 'test_id'
        error_message = 'Test error'

        def failing_operation():
            raise SQLAlchemyError('Database error')

        result = UtilizationController._persist_operation(
            failing_operation, utilization_id, error_message
        )

        assert result.success is False
        assert result.error_message is not None
        mock_rollback.assert_called_once()
        mock_log.assert_called_once()
        mock_commit.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.log.exception')
    @patch('ckanext.feedback.controllers.utilization.session.rollback')
    @patch('ckanext.feedback.controllers.utilization.session.commit')
    def test_persist_operation_with_generic_exception(
        self, mock_commit, mock_rollback, mock_log
    ):
        """Test _persist_operation with generic Exception"""
        utilization_id = 'test_id'
        error_message = 'Test error'

        def failing_operation():
            raise ValueError('Generic error')

        result = UtilizationController._persist_operation(
            failing_operation, utilization_id, error_message
        )

        assert result.success is False
        assert result.error_message is not None
        mock_rollback.assert_called_once()
        mock_log.assert_called_once()
        mock_commit.assert_not_called()

    @patch('ckanext.feedback.controllers.utilization.helpers.flash_error')
    @patch('ckanext.feedback.controllers.utilization.toolkit.redirect_to')
    def test_handle_validation_error_without_message(
        self, mock_redirect_to, mock_flash_error
    ):
        """Test _handle_validation_error when error_message is None"""
        utilization_id = 'test_id'
        category = 'test_category'
        content = 'test_content'

        UtilizationController._handle_validation_error(
            utilization_id, None, category, content, None
        )

        mock_flash_error.assert_not_called()
        mock_redirect_to.assert_called_once()

    @patch('ckanext.feedback.controllers.utilization.request.form')
    @patch('ckanext.feedback.controllers.utilization.request.files.get')
    @patch('ckanext.feedback.controllers.utilization.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.utilization.validate_service.validate_comment')
    def test_process_comment_input_without_form_data(
        self,
        mock_validate_comment,
        mock_is_recaptcha_verified,
        mock_files,
        mock_form,
    ):
        """Test _process_comment_input when form_data is None (extracted internally)"""
        utilization_id = 'test_id'
        category = 'REQUEST'
        content = 'test content'

        mock_form.get.side_effect = [category, content, None]
        mock_files.return_value = None
        mock_is_recaptcha_verified.return_value = True
        mock_validate_comment.return_value = None

        result = UtilizationController._process_comment_input(
            'image-upload', utilization_id, None
        )

        assert result.form_data['category'] == category
        assert result.form_data['content'] == content
        assert result.error_response is None
