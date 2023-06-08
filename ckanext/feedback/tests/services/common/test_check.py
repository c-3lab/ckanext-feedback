from unittest.mock import patch

import pytest
import six
from ckan import model
from ckan.model import User
from ckan.tests import factories
from flask import Flask, g

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.management import ManagementController
from ckanext.feedback.services.common.check import check_administrator

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestResourceController:
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
        user.sysadmin = False
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        @check_administrator
        def dummy_function():
            return "function is called"

        g.userobj = None
        dummy_function()

        mock_toolkit.abort.assert_called_once()

        with self.app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            result = dummy_function()

        assert result == "function is called"
