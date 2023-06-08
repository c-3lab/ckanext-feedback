'''
Tests for plugin.py.

Tests are written using the pytest library (https://docs.pytest.org), and you
should read the testing guidelines in the CKAN docs:
https://docs.ckan.org/en/2.9/contributing/testing.html

To write tests for your extension you should install the pytest-ckan package:

    pip install pytest-ckan

This will allow you to use CKAN specific fixtures on your tests.

For instance, if your test involves database access you can use `clean_db` to
reset the database:

    import pytest

    from ckan.tests import factories

    @pytest.mark.usefixtures("clean_db")
    def test_some_action():

        dataset = factories.Dataset()

        # ...

For functional tests that involve requests to the application, you can use the
`app` fixture:

    from ckan.plugins import toolkit

    def test_some_endpoint(app):

        url = toolkit.url_for('myblueprint.some_endpoint')

        response = app.get(url)

        assert response.status_code == 200


To temporary patch the CKAN configuration for the duration of a
test you can use:

    import pytest

    @pytest.mark.ckan_config("ckanext.myext.some_key", "some_value")
    def test_some_action():
        pass
'''

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

from ckanext.feedback.plugin import FeedbackPlugin
from ckanext.feedback.command import feedback

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestPlugin:
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_commands(self):
        result = FeedbackPlugin.get_commands(self)
        assert result == [feedback.feedback]

    @patch('ckanext.feedback.plugin.toolkit')
    @patch('ckanext.feedback.plugin.config')
    @patch('ckanext.feedback.plugin.download')
    @patch('ckanext.feedback.plugin.resource')
    @patch('ckanext.feedback.plugin.utilization')
    @patch('ckanext.feedback.plugin.management')
    def test_get_blueprint(self, mock_management, mock_utilization, mock_resource, mock_download, mock_config, mock_toolkit):
        instance = FeedbackPlugin()
        mock_management.get_management_blueprint.return_value = "management_bp"
        mock_download.get_download_blueprint.return_value = "download_bp"
        mock_resource.get_resource_comment_blueprint.return_value = "resource_bp"
        mock_utilization.get_utilization_blueprint.return_value = "utilization_bp"

        expected_blueprints = ["download_bp", "resource_bp", "utilization_bp", "management_bp"]

        actual_blueprints = instance.get_blueprint()

        assert actual_blueprints == expected_blueprints

        mock_toolkit.asbool.side_effect = [False, False, False]
        expected_blueprints = ["management_bp"]
        actual_blueprints = instance.get_blueprint()

        assert actual_blueprints == expected_blueprints

    def test_is_disabled_repeated_post_on_resource(self):
        assert FeedbackPlugin.is_disabled_repeated_post_on_resource(self) == False
