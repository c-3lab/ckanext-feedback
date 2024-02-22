from unittest.mock import patch

import pytest
import six
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
from ckanext.feedback.services.common.check import (
    check_administrator,
    is_organization_admin,
    has_organization_admin_role,
)

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestCheck:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)

    @patch('ckanext.feedback.services.common.check.toolkit')
    def test_check_administrator(self, mock_toolkit):
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        user.sysadmin = True
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        @check_administrator
        def dummy_function():
            return 'function is called'

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            result = dummy_function()

        assert result == 'function is called'

    @patch('ckanext.feedback.services.common.check.toolkit')
    def test_check_administrator_with_org_admin_user(self, mock_toolkit):
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        organization_dict = factories.Organization()
        organization = model.Group.get(organization_dict['id'])
        member = model.Member(
            group=organization,
            group_id=organization.id,
            table_id=user.id,
            capacity='admin',
            table_name='user',
        )
        model.Session.add(member)
        model.Session.commit()

        @check_administrator
        def dummy_function():
            return 'function is called'

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
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

    @patch('ckanext.feedback.services.common.check.toolkit')
    def test_check_administrator_with_user(self, mock_toolkit):
        @check_administrator
        def dummy_function():
            return 'function is called'

        user_dict = factories.User()
        user = User.get(user_dict['id'])
        g.userobj = user
        dummy_function()

        mock_toolkit.abort.assert_called_with(
            404,
            _(
                'The requested URL was not found on the server. If you entered the'
                ' URL manually please check your spelling and try again.'
            ),
        )

    def test_is_organization_admin_with_user(self):
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        user.sysadmin = False
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        organization_dict = factories.Organization()
        organization = model.Group.get(organization_dict['id'])
        member = model.Member(
            group=organization,
            group_id=organization.id,
            table_id=user.id,
            capacity='admin',
            table_name='user',
        )
        model.Session.add(member)
        model.Session.commit()
        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            result = is_organization_admin()

        assert result is True

    def test_is_organization_admin_without_user(self):
        g.userobj = None
        result = is_organization_admin()

        assert result is False

    def test_has_organization_admin_role_with_user(self):
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        user.sysadmin = False
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        organization_dict1 = factories.Organization()
        organization_dict2 = factories.Organization()
        organization_dict3 = factories.Organization()
        organization1 = model.Group.get(organization_dict1['id'])
        organization2 = model.Group.get(organization_dict2['id'])
        organization3 = model.Group.get(organization_dict3['id'])
        member1 = model.Member(
            group=organization1,
            group_id=organization1.id,
            table_id=user.id,
            capacity='admin',
            table_name='user',
        )
        model.Session.add(member1)
        member3 = model.Member(
            group=organization1,
            group_id=organization3.id,
            table_id=user.id,
            capacity='member',
            table_name='user',
        )
        model.Session.add(member1)
        model.Session.add(member3)
        model.Session.commit()
        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            assert has_organization_admin_role(organization1.id) is True
            assert has_organization_admin_role(organization2.id) is False
            assert has_organization_admin_role(organization3.id) is False

    def test_has_organization_admin_role_without_user(self):
        organization_dict1 = factories.Organization()
        organization1 = model.Group.get(organization_dict1['id'])

        g.userobj = None
        result = has_organization_admin_role(organization1.id)

        assert result is False
