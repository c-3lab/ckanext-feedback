from unittest.mock import patch, mock_open
from types import SimpleNamespace
import json
import os

from ckan.common import config

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

    def setup_method(self, method):
        if os.path.isfile('/etc/ckan/feedback_config.json'):
            os.remove('/etc/ckan/feedback_config.json')

    def test_update_config_without_feedback_config_file(self):
        instance = FeedbackPlugin()
        instance.update_config(config)
        assert instance.is_feedback_config_file is False

    def test_update_config_with_feedback_config_file(self):
        instance = FeedbackPlugin()
        feedback_config = {
            'modules': {
                'utilizations': {
                    'enable': True,
                    'enable_orgs': []
                },
                'resources': {
                    'enable': True,
                    'enable_orgs': [],
                    'comments': {
                        'repeat_post_limit': {
                            'enable': False,
                            'enable_orgs': []
                        }
                    }
                },
                'downloads': {
                    'enable': True,
                    'enable_orgs': [],
                }
            }
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        instance.update_config(config)
        assert instance.is_feedback_config_file is True
        assert config.get('ckan.feedback.utilizations.enable') is True
        assert config.get('ckan.feedback.utilizations.enable_orgs') == []
        assert config.get('ckan.feedback.resources.enable') is True
        assert config.get('ckan.feedback.resources.enable_orgs') == []
        assert config.get('ckan.feedback.resources.comment.repeat_post_limit.enable') is False
        assert config.get('ckan.feedback.resources.comment.repeat_post_limit.enable_orgs') == []
        assert config.get('ckan.feedback.downloads.enable') is True
        assert config.get('ckan.feedback.downloads.enable_orgs') == []

    @patch('ckanext.feedback.plugin.toolkit')
    def test_update_config_attribute_error(self, mock_toolkit):
        instance = FeedbackPlugin()
        feedback_config = {
            'modules': {}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        instance.update_config(config)
        mock_toolkit.error_shout.call_count == 4

    @patch('ckanext.feedback.plugin.toolkit')
    def test_update_config_json_decode_error(self, mock_toolkit):
        instance = FeedbackPlugin()
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            f.write('{"modules":')

        instance.update_config(config)
        mock_toolkit.error_shout.assert_called_once_with('The feedback config file not decoded correctly')

    def test_get_commands(self):
        result = FeedbackPlugin.get_commands(self)
        assert result == [feedback.feedback]


#    @patch('builtins.open', new_callable=mock_open)
#    @patch('ckanext.feedback.plugin.config')
#    @patch('ckanext.feedback.plugin.json')
#    def test_update_config(self, mock_json, mock_config, open_mock):
#        feedback_config = {
#            'modules': {
#                'downloads': {
#                    'enable': True,
#                    'enable_orgs': []
#                }
#            }
#        }
#        instance = FeedbackPlugin()
#        mock_config.get.return_value = '/etc/ckan'
#        mock_json.load.return_value = feedback_config.get('modules', {})
#        instance.update_config(mock_config)
#
#        mock_json.load.assert_called_once_with(feedback_config, object_hook=lambda d: SimpleNamespace(**d))

#    @patch('ckanext.feedback.plugin.toolkit')
#    @patch('ckanext.feedback.plugin.download')
#    @patch('ckanext.feedback.plugin.resource')
#    @patch('ckanext.feedback.plugin.utilization')
#    @patch('ckanext.feedback.plugin.management')
#    def test_get_blueprint(
#        self,
#        mock_management,
#        mock_utilization,
#        mock_resource,
#        mock_download,
#        mock_toolkit,
#    ):
#        instance = FeedbackPlugin()
#        mock_management.get_management_blueprint.return_value = 'management_bp'
#        mock_download.get_download_blueprint.return_value = 'download_bp'
#        mock_resource.get_resource_comment_blueprint.return_value = 'resource_bp'
#        mock_utilization.get_utilization_blueprint.return_value = 'utilization_bp'
#
#        expected_blueprints = [
#            'download_bp',
#            'resource_bp',
#            'utilization_bp',
#            'management_bp',
#        ]
#
#        actual_blueprints = instance.get_blueprint()
#
#        assert actual_blueprints == expected_blueprints
#
#        mock_toolkit.asbool.side_effect = [False, False, False]
#        expected_blueprints = ['management_bp']
#        actual_blueprints = instance.get_blueprint()
#
#        assert actual_blueprints == expected_blueprints
#
#    def test_is_disabled_repeated_post_on_resource(self):
#        assert FeedbackPlugin.is_disabled_repeated_post_on_resource(self) is False
