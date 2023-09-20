from unittest.mock import patch

import pytest
from ckan import model

from ckanext.feedback.command import feedback
from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.plugin import FeedbackPlugin

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
    @patch('ckanext.feedback.plugin.download')
    @patch('ckanext.feedback.plugin.resource')
    @patch('ckanext.feedback.plugin.utilization')
    @patch('ckanext.feedback.plugin.management')
    def test_get_blueprint(
        self,
        mock_management,
        mock_utilization,
        mock_resource,
        mock_download,
        mock_toolkit,
    ):
        instance = FeedbackPlugin()
        mock_management.get_management_blueprint.return_value = 'management_bp'
        mock_download.get_download_blueprint.return_value = 'download_bp'
        mock_resource.get_resource_comment_blueprint.return_value = 'resource_bp'
        mock_utilization.get_utilization_blueprint.return_value = 'utilization_bp'

        expected_blueprints = [
            'download_bp',
            'resource_bp',
            'utilization_bp',
            'management_bp',
        ]

        actual_blueprints = instance.get_blueprint()

        assert actual_blueprints == expected_blueprints

        mock_toolkit.asbool.side_effect = [False, False, False]
        expected_blueprints = ['management_bp']
        actual_blueprints = instance.get_blueprint()

        assert actual_blueprints == expected_blueprints

    def test_is_disabled_repeated_post_on_resource(self):
        assert FeedbackPlugin.is_disabled_repeated_post_on_resource(self) is False
