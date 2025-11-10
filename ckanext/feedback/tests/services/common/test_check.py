from unittest.mock import patch

import pytest
from ckan import model
from ckan.common import _
from ckan.model import User
from flask import g

from ckanext.feedback.services.common.check import (
    check_administrator,
    get_authorized_package,
    has_organization_admin_role,
    is_organization_admin,
    require_package_access,
    require_resource_package_access,
    user_has_organization_admin_role,
)
from ckanext.feedback.utils.auth import create_auth_context


@pytest.mark.db_test
@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestCheck:

    @patch('flask_login.utils._get_user')
    def test_check_administrator(
        self, current_user, sysadmin, mock_current_user_fixture
    ):
        mock_current_user_fixture(current_user, sysadmin)

        @check_administrator
        def dummy_function():
            return 'function is called'

        result = dummy_function()
        assert result == 'function is called'

    @patch('flask_login.utils._get_user')
    def test_check_administrator_with_org_admin_user(
        self, current_user, user, organization, mock_current_user_fixture
    ):
        user_obj = User.get(user['id'])
        mock_current_user_fixture(current_user, user)

        organization_obj = model.Group.get(organization['id'])
        member = model.Member(
            group=organization_obj,
            group_id=organization_obj.id,
            table_id=user_obj.id,
            capacity='admin',
            table_name='user',
        )
        model.Session.add(member)
        model.Session.commit()

        @check_administrator
        def dummy_function():
            return 'function is called'

        result = dummy_function()
        assert result == 'function is called'

    @patch('ckanext.feedback.services.common.check.toolkit')
    def test_check_administrator_without_user(self, mock_toolkit):
        @check_administrator
        def dummy_function():
            return 'function is called'

        g.userobj = None
        dummy_function()

        mock_toolkit.abort.assert_called_with(
            404,
            _(
                'The requested URL was not found on the server. If you entered the'
                ' URL manually please check your spelling and try again.'
            ),
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.services.common.check.toolkit')
    def test_check_administrator_with_user(
        self, mock_toolkit, current_user, user, mock_current_user_fixture
    ):
        @check_administrator
        def dummy_function():
            return 'function is called'

        mock_current_user_fixture(current_user, user)
        dummy_function()

        mock_toolkit.abort.assert_called_with(
            404,
            _(
                'The requested URL was not found on the server. If you entered the'
                ' URL manually please check your spelling and try again.'
            ),
        )

    @patch('flask_login.utils._get_user')
    def test_is_organization_admin_with_user(
        self, current_user, user, organization, mock_current_user_fixture
    ):
        user_obj = User.get(user['id'])
        mock_current_user_fixture(current_user, user)

        organization_obj = model.Group.get(organization['id'])
        member = model.Member(
            group=organization_obj,
            group_id=organization_obj.id,
            table_id=user_obj.id,
            capacity='admin',
            table_name='user',
        )
        model.Session.add(member)
        model.Session.commit()

        result = is_organization_admin()
        assert result is True

    def test_is_organization_admin_without_user(self):
        g.userobj = None
        result = is_organization_admin()

        assert result is False

    @patch('flask_login.utils._get_user')
    def test_has_organization_admin_role_with_user(
        self, current_user, user, organization, mock_current_user_fixture
    ):
        user_obj = User.get(user['id'])
        mock_current_user_fixture(current_user, user)

        organization1 = model.Group.get(organization['id'])

        organization2 = model.Group(
            name='test-org-2', title='Test Organization 2', type='organization'
        )
        model.Session.add(organization2)
        organization3 = model.Group(
            name='test-org-3', title='Test Organization 3', type='organization'
        )
        model.Session.add(organization3)
        model.Session.flush()

        member1 = model.Member(
            group=organization1,
            group_id=organization1.id,
            table_id=user_obj.id,
            capacity='admin',
            table_name='user',
        )
        model.Session.add(member1)
        member3 = model.Member(
            group=organization3,
            group_id=organization3.id,
            table_id=user_obj.id,
            capacity='member',
            table_name='user',
        )
        model.Session.add(member3)
        model.Session.commit()

        assert has_organization_admin_role(organization1.id) is True
        assert has_organization_admin_role(organization2.id) is False
        assert has_organization_admin_role(organization3.id) is False

    def test_has_organization_admin_role_without_user(self, organization):
        organization_obj = model.Group.get(organization['id'])

        g.userobj = None
        result = has_organization_admin_role(organization_obj.id)

        assert result is False

    def test_user_has_organization_admin_role_without_user_id(self, organization):
        organization_obj = model.Group.get(organization['id'])
        assert user_has_organization_admin_role(None, organization_obj.id) is False

    def test_user_has_organization_admin_role_with_invalid_user(self, organization):
        organization_obj = model.Group.get(organization['id'])
        assert (
            user_has_organization_admin_role('invalid-user-id', organization_obj.id)
            is False
        )

    def test_user_has_organization_admin_role_with_sysadmin(
        self, sysadmin, organization
    ):
        organization_obj = model.Group.get(organization['id'])
        assert (
            user_has_organization_admin_role(sysadmin['id'], organization_obj.id)
            is True
        )

    def test_user_has_organization_admin_role_with_org_admin_and_non_admin(
        self, user, organization, another_organization
    ):
        user_obj = User.get(user['id'])
        organization_obj1 = model.Group.get(organization['id'])
        organization_obj2 = model.Group.get(another_organization['id'])

        member = model.Member(
            group=organization_obj1,
            group_id=organization_obj1.id,
            table_id=user_obj.id,
            capacity='admin',
            table_name='user',
        )
        model.Session.add(member)
        model.Session.commit()

        assert (
            user_has_organization_admin_role(user['id'], organization_obj1.id) is True
        )
        assert (
            user_has_organization_admin_role(user['id'], organization_obj2.id) is False
        )

    def test_create_auth_context(self):
        context = create_auth_context()

        assert 'model' in context
        assert 'session' in context
        assert 'for_view' in context

        assert context['model'] is not None
        assert context['session'] is not None

        assert context['for_view'] is True

        import ckan.model as expected_model

        assert context['model'] == expected_model

        assert context['session'] == expected_model.Session

    @patch('ckanext.feedback.services.common.check.get_action')
    def test_get_authorized_package_public_package(self, mock_get_action):
        package_id = 'test_package_id'
        context = create_auth_context()
        expected_package = {'id': package_id, 'name': 'test-package'}

        mock_get_action.return_value = lambda ctx, data_dict: expected_package

        result = get_authorized_package(package_id, context)
        assert result == expected_package

    @patch('ckanext.feedback.services.common.check.get_action')
    def test_get_authorized_package_returns_complete_package_data(
        self, mock_get_action
    ):
        package_id = 'complete_package_id'
        context = create_auth_context()

        expected_package = {
            'id': package_id,
            'name': 'test-package',
            'title': 'Test Package',
            'private': False,
            'owner_org': 'test-org-id',
            'resources': [
                {'id': 'resource-1', 'name': 'Resource 1'},
                {'id': 'resource-2', 'name': 'Resource 2'},
            ],
            'tags': [{'name': 'test'}, {'name': 'data'}],
        }

        mock_get_action.return_value = lambda ctx, data_dict: expected_package

        result = get_authorized_package(package_id, context)

        assert result['id'] == package_id
        assert result['name'] == 'test-package'
        assert result['title'] == 'Test Package'
        assert result['private'] is False
        assert result['owner_org'] == 'test-org-id'
        assert len(result['resources']) == 2
        assert len(result['tags']) == 2

        assert result == expected_package

    @patch('ckanext.feedback.services.common.check.get_action')
    def test_get_authorized_package_context_is_passed_correctly(self, mock_get_action):
        package_id = 'test_package_id'
        context = create_auth_context()

        received_context = None
        received_data_dict = None

        def mock_package_show(ctx, data_dict):
            nonlocal received_context, received_data_dict
            received_context = ctx
            received_data_dict = data_dict
            return {'id': package_id}

        mock_get_action.return_value = mock_package_show

        get_authorized_package(package_id, context)

        assert received_context == context
        assert received_data_dict == {'id': package_id}

    @patch('ckanext.feedback.services.common.check.get_action')
    def test_require_package_access_public_package(self, mock_get_action):
        package_id = 'test_package_id'
        context = create_auth_context()

        mock_get_action.return_value = lambda ctx, data_dict: {'id': package_id}

        try:
            require_package_access(package_id, context)
        except Exception as e:
            pytest.fail(f"require_package_access raised {e} unexpectedly")

    @patch('ckanext.feedback.services.common.check.toolkit')
    @patch('ckanext.feedback.services.common.check.get_action')
    def test_get_authorized_package_private_package_unauthorized(
        self, mock_get_action, mock_toolkit
    ):
        from ckan.logic import NotAuthorized

        package_id = 'private_package_id'
        context = create_auth_context()

        mock_get_action.return_value = lambda ctx, data_dict: (_ for _ in ()).throw(
            NotAuthorized('User not authorized')
        )

        get_authorized_package(package_id, context)

        mock_toolkit.abort.assert_called_once()
        assert mock_toolkit.abort.call_args[0][0] == 404

    @patch('ckanext.feedback.services.common.check.toolkit')
    @patch('ckanext.feedback.services.common.check.get_action')
    def test_get_authorized_package_not_found(self, mock_get_action, mock_toolkit):
        from ckan.logic import NotFound

        package_id = 'nonexistent_package_id'
        context = create_auth_context()

        mock_get_action.return_value = lambda ctx, data_dict: (_ for _ in ()).throw(
            NotFound('Package not found')
        )

        get_authorized_package(package_id, context)

        mock_toolkit.abort.assert_called_once()
        assert mock_toolkit.abort.call_args[0][0] == 404

    @patch('ckanext.feedback.services.resource.comment.get_resource')
    @patch('ckanext.feedback.services.common.check.get_action')
    def test_require_resource_package_access_public_package(
        self, mock_get_action, mock_get_resource
    ):
        from unittest.mock import MagicMock

        resource_id = 'test_resource_id'
        package_id = 'test_package_id'
        context = create_auth_context()

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = package_id
        mock_get_resource.return_value = mock_resource

        mock_get_action.return_value = lambda ctx, data_dict: {'id': package_id}

        try:
            require_resource_package_access(resource_id, context)
        except Exception as e:
            pytest.fail(f"require_resource_package_access raised {e} unexpectedly")

    @patch('ckanext.feedback.services.common.check.toolkit')
    @patch('ckanext.feedback.services.resource.comment.get_resource')
    @patch('ckanext.feedback.services.common.check.get_action')
    def test_require_resource_package_access_private_package_unauthorized(
        self, mock_get_action, mock_get_resource, mock_toolkit
    ):
        from unittest.mock import MagicMock

        from ckan.logic import NotAuthorized

        resource_id = 'test_resource_id'
        package_id = 'private_package_id'
        context = create_auth_context()

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = package_id
        mock_get_resource.return_value = mock_resource

        mock_get_action.return_value = lambda ctx, data_dict: (_ for _ in ()).throw(
            NotAuthorized('User not authorized')
        )

        require_resource_package_access(resource_id, context)

        mock_toolkit.abort.assert_called_once()
        assert mock_toolkit.abort.call_args[0][0] == 404

    @patch('ckanext.feedback.services.resource.comment.get_resource')
    def test_require_resource_package_access_resource_not_found(
        self, mock_get_resource
    ):
        resource_id = 'nonexistent_resource_id'
        context = create_auth_context()

        mock_get_resource.return_value = None

        try:
            require_resource_package_access(resource_id, context)
        except Exception as e:
            pytest.fail(f"require_resource_package_access raised {e} unexpectedly")
