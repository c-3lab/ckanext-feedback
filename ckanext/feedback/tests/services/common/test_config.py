import json
import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from ckan.common import config
from ckan.plugins import toolkit
from ckan.plugins.toolkit import ValidationError

from ckanext.feedback.command import feedback
from ckanext.feedback.plugin import FeedbackPlugin
from ckanext.feedback.services.common.config import (
    CONFIG_HANDLER_PATH,
    FeedbackConfig,
    download_handler,
)

ORG_NAME_A = 'org-name-a'
ORG_NAME_B = 'org-name-b'
ORG_NAME_C = 'org-name-c'
ORG_NAME_D = 'org-name-d'


@pytest.mark.usefixtures("cleanup_feedback_config")
class TestCheck:
    @patch('ckanext.feedback.services.common.config.import_string')
    def test_seted_download_handler(self, mock_import_string):
        toolkit.config['ckan.feedback.download_handler'] = CONFIG_HANDLER_PATH
        download_handler()
        mock_import_string.assert_called_once_with(CONFIG_HANDLER_PATH, silent=True)

    def test_not_seted_download_handler(self):
        toolkit.config.pop('ckan.feedback.download_handler', '')
        assert download_handler() is None

    @patch('ckanext.feedback.services.common.config.DownloadsConfig.load_config')
    @patch('ckanext.feedback.services.common.config.ResourceCommentConfig.load_config')
    @patch('ckanext.feedback.services.common.config.UtilizationConfig.load_config')
    @patch(
        'ckanext.feedback.services.common.config.UtilizationCommentConfig.load_config'
    )
    @patch('ckanext.feedback.services.common.config.ReCaptchaConfig.load_config')
    @patch('ckanext.feedback.services.common.config.NoticeEmailConfig.load_config')
    def test_load_feedback_config_with_feedback_config_file(
        self,
        mock_DownloadsConfig_load_config,
        mock_ResourceCommentConfig_load_config,
        mock_UtilizationCommentConfig_load_config,
        mock_UtilizationConfig_load_config,
        mock_ReCaptchaConfig_load_config,
        mock_NoticeEmailConfig_load_config,
    ):

        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is False

        # without .ini file
        feedback_config = {'modules': {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True
        mock_DownloadsConfig_load_config.assert_called_once()
        mock_ResourceCommentConfig_load_config.assert_called_once()
        mock_UtilizationCommentConfig_load_config.assert_called_once()
        mock_UtilizationConfig_load_config.assert_called_once()
        mock_ReCaptchaConfig_load_config.assert_called_once()
        mock_NoticeEmailConfig_load_config.assert_called_once()
        os.remove('/srv/app/feedback_config.json')

    @patch('ckanext.feedback.plugin.toolkit')
    def test_update_config_attribute_error(self, mock_toolkit):
        feedback_config = {'modules': {}}

        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        mock_toolkit.error_shout.assert_not_called()
        os.remove('/srv/app/feedback_config.json')

    @patch('ckanext.feedback.services.common.config.toolkit')
    def test_update_config_json_decode_error(self, mock_toolkit):
        with open('/srv/app/feedback_config.json', 'w') as f:
            f.write('{"modules":')
        with pytest.raises(json.JSONDecodeError):
            FeedbackConfig().load_feedback_config()

        call_args = mock_toolkit.error_shout.call_args[0][0]
        assert 'The feedback config file not decoded correctly' in call_args
        assert 'Expecting' in call_args or 'line' in call_args

    @patch('ckanext.feedback.services.common.config.toolkit.error_shout')
    def test_load_feedback_config_top_level_not_dict(self, mock_error_shout):
        feedback_config = [{"modules": {}}]

        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        with pytest.raises(ValidationError):
            FeedbackConfig().load_feedback_config()

        call_args = mock_error_shout.call_args[0][0]
        assert 'The feedback config file validation failed:' in call_args
        assert 'feedback_config.json must be a JSON object' in call_args

    def test_load_feedback_config_modules_value_not_dict(self):
        feedback_config = {"modules": "not_dict"}

        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        with pytest.raises(ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert 'object' in error_message.lower() or 'dict' in error_message.lower()

    def test_load_config_invalid_module_name(self):
        feedback_config = {
            "modules": {
                "invalid_module_name": {"enable": True},
                "utilizations": {"enable": True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        with pytest.raises(ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            'invalid' in error_message.lower() or 'module' in error_message.lower()
        ), f"Expected error about invalid module, but got: {error_message}"
        assert (
            'invalid_module_name' in error_message
        ), f"Expected error to mention 'invalid_module_name', but got: {error_message}"

    def test_get_commands(self):
        result = FeedbackPlugin.get_commands(self)
        assert result == [feedback.feedback]

    @patch('ckanext.feedback.services.common.config.organization_service')
    def test_load_feedback_config_and_is_enable(self, mock_organization_service):
        # No description of settings
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.enable_orgs', None)
        config.pop('ckan.feedback.resources.disable_orgs', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is None
        assert config.get('ckan.feedback.resources.enable_orgs', None) is None
        assert config.get('ckan.feedback.resources.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().resource_comment.is_enable() is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is True

        # Write enable = True in ckan.ini
        config['ckan.feedback.resources.enable'] = True

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) is None
        assert config.get('ckan.feedback.resources.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().resource_comment.is_enable() is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is True

        # Write enable = False in ckan.ini
        config['ckan.feedback.resources.enable'] = False

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is False
        assert config.get('ckan.feedback.resources.enable_orgs', None) is None
        assert config.get('ckan.feedback.resources.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().resource_comment.is_enable() is False
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is False
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is False
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is False
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is False

        # enable has an invalid value
        config['ckan.feedback.resources.enable'] = "invalid_value"

        FeedbackConfig().load_feedback_config()

        with pytest.raises(ValidationError) as exc_info:
            FeedbackConfig().resource_comment.is_enable()

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == (
            "The value of the \"enable\" key is invalid. "
            "Please specify a boolean value such as "
            "`true` or `false` for the \"enable\" key."
        )

        # The module is not listed in the feedback_config.json
        config.pop('ckan.feedback.resources.enable', None)

        feedback_config = {"modules": {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is None
        assert config.get('ckan.feedback.resources.enable_orgs', None) is None
        assert config.get('ckan.feedback.resources.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_A})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_B})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_C})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_D})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is True
        os.remove('/srv/app/feedback_config.json')

        # The "enable" key is set to True in feedback_config.json
        config.pop('ckan.feedback.resources.enable', None)

        feedback_config = {"modules": {"resources": {"enable": True}}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) is None
        assert config.get('ckan.feedback.resources.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_A})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_B})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_C})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_D})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is True
        os.remove('/srv/app/feedback_config.json')

        # The "enable_orgs" key is listed in feedback_config.json
        config.pop('ckan.feedback.resources.enable', None)

        feedback_config = {
            "modules": {
                "resources": {"enable": True, "enable_orgs": [ORG_NAME_A, ORG_NAME_B]}
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) == [
            ORG_NAME_A,
            ORG_NAME_B,
        ]
        assert config.get('ckan.feedback.resources.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_A})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_B})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_C})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is False
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_D})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is False
        os.remove('/srv/app/feedback_config.json')

        # The "disable_orgs" key is listed in feedback_config.json
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.enable_orgs', None)

        feedback_config = {
            "modules": {
                "resources": {"enable": True, "disable_orgs": [ORG_NAME_A, ORG_NAME_B]}
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) is None
        assert config.get('ckan.feedback.resources.disable_orgs', None) == [
            ORG_NAME_A,
            ORG_NAME_B,
        ]
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_A})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is False
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_B})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is False
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_C})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_D})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is True
        os.remove('/srv/app/feedback_config.json')

        # Both "enable_orgs" and "disable_orgs" are listed in feedback_config.json
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.disable_orgs', None)

        feedback_config = {
            "modules": {
                "resources": {
                    "enable": True,
                    "enable_orgs": [ORG_NAME_A, ORG_NAME_B],
                    "disable_orgs": [ORG_NAME_C],
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) == [
            ORG_NAME_A,
            ORG_NAME_B,
        ]
        assert config.get('ckan.feedback.resources.disable_orgs', None) == [ORG_NAME_C]
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_A})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_B})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_C})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is False
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_D})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is True
        os.remove('/srv/app/feedback_config.json')

        # The same organization is listed in both
        # "enable_orgs" and "disable_orgs" in feedback_config.json
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.enable_orgs', None)
        config.pop('ckan.feedback.resources.disable_orgs', None)

        feedback_config = {
            "modules": {
                "resources": {
                    "enable": True,
                    "enable_orgs": [ORG_NAME_A, ORG_NAME_B],
                    "disable_orgs": [ORG_NAME_A],
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) == [
            ORG_NAME_A,
            ORG_NAME_B,
        ]
        assert config.get('ckan.feedback.resources.disable_orgs', None) == [ORG_NAME_A]
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_A})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is False
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_B})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_C})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is True
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_D})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is True
        os.remove('/srv/app/feedback_config.json')

        # The "enable" key is set to False in feedback_config.json
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.enable_orgs', None)
        config.pop('ckan.feedback.resources.disable_orgs', None)

        feedback_config = {"modules": {"resources": {"enable": False}}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is False
        assert config.get('ckan.feedback.resources.enable_orgs', None) is None
        assert config.get('ckan.feedback.resources.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is False
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_A})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is False
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_B})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is False
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_C})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is False
        mock_organization_service.get_organization_name_by_id.return_value = (
            SimpleNamespace(**{'name': ORG_NAME_D})
        )
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is False
        os.remove('/srv/app/feedback_config.json')

        # The specified organization was not found
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.enable_orgs', None)
        config.pop('ckan.feedback.resources.disable_orgs', None)

        feedback_config = {"modules": {"resources": {"enable": True}}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) is None
        assert config.get('ckan.feedback.resources.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        mock_organization_service.get_organization_name_by_id.return_value = None
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is False
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is False
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is False
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is False
        os.remove('/srv/app/feedback_config.json')

        # The "enable" key does not exist
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.enable_orgs', None)
        config.pop('ckan.feedback.resources.disable_orgs', None)

        feedback_config = {"modules": {"resources": {}}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        with pytest.raises(ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "modules.resources must not be empty"
        os.remove('/srv/app/feedback_config.json')

        # The value of "enable_orgs" is not an array of strings
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.enable_orgs', None)
        config.pop('ckan.feedback.resources.disable_orgs', None)

        feedback_config = {
            "modules": {"resources": {"enable": True, "enable_orgs": ORG_NAME_A}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        with pytest.raises(ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == 'modules.resources.enable_orgs must be a list of strings, got str'
        )
        os.remove('/srv/app/feedback_config.json')

        # The value of "disable_orgs" is not an array of strings
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.enable_orgs', None)
        config.pop('ckan.feedback.resources.disable_orgs', None)

        feedback_config = {
            "modules": {"resources": {"enable": True, "disable_orgs": ORG_NAME_A}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        with pytest.raises(ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == 'modules.resources.disable_orgs must be a list of strings, got str'
        )
        os.remove('/srv/app/feedback_config.json')

    @patch('ckanext.feedback.services.common.config.organization_service')
    def test_module_default_config(self, mock_organization_service):
        # utilization(ckan.ini)
        config.pop('ckan.feedback.utilizations.enable', None)
        config.pop('ckan.feedback.utilizations.enable_orgs', None)
        config.pop('ckan.feedback.utilizations.disable_orgs', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.utilizations.enable', None) is None
        assert config.get('ckan.feedback.utilizations.enable_orgs', None) is None
        assert config.get('ckan.feedback.utilizations.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().utilization.is_enable() is True
        assert FeedbackConfig().utilization.is_enable(ORG_NAME_A) is True
        assert FeedbackConfig().utilization.is_enable(ORG_NAME_B) is True
        assert FeedbackConfig().utilization.is_enable(ORG_NAME_C) is True
        assert FeedbackConfig().utilization.is_enable(ORG_NAME_D) is True

        # utilization(feedback_config.json)
        feedback_config = {"modules": {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.utilizations.enable', None) is None
        assert config.get('ckan.feedback.utilizations.enable_orgs', None) is None
        assert config.get('ckan.feedback.utilizations.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().utilization.is_enable() is True
        assert FeedbackConfig().utilization.is_enable(ORG_NAME_A) is True
        assert FeedbackConfig().utilization.is_enable(ORG_NAME_B) is True
        assert FeedbackConfig().utilization.is_enable(ORG_NAME_C) is True
        assert FeedbackConfig().utilization.is_enable(ORG_NAME_D) is True
        os.remove('/srv/app/feedback_config.json')

        # repeated_post_limit(ckan.ini)
        config.pop('ckan.feedback.resources.comment.repeated_post_limit.enable', None)
        config.pop(
            'ckan.feedback.resources.comment.repeated_post_limit.enable_orgs', None
        )
        config.pop(
            'ckan.feedback.resources.comment.repeated_post_limit.disable_orgs', None
        )

        FeedbackConfig().load_feedback_config()

        assert (
            config.get(
                'ckan.feedback.resources.comment.repeated_post_limit.enable', None
            )
            is None
        )
        assert (
            config.get(
                'ckan.feedback.resources.comment.repeated_post_limit.enable_orgs', None
            )
            is None
        )
        assert (
            config.get(
                'ckan.feedback.resources.comment.repeated_post_limit.disable_orgs', None
            )
            is None
        )
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().resource_comment.repeat_post_limit.is_enable() is False
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(ORG_NAME_A)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(ORG_NAME_B)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(ORG_NAME_C)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(ORG_NAME_D)
            is False
        )

        # repeated_post_limit(feedback_config.json)
        feedback_config = {"modules": {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert (
            config.get(
                'ckan.feedback.resources.comment.repeated_post_limit.enable', None
            )
            is None
        )
        assert (
            config.get(
                'ckan.feedback.resources.comment.repeated_post_limit.enable_orgs', None
            )
            is None
        )
        assert (
            config.get(
                'ckan.feedback.resources.comment.repeated_post_limit.disable_orgs', None
            )
            is None
        )
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.repeat_post_limit.is_enable() is False
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(ORG_NAME_A)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(ORG_NAME_B)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(ORG_NAME_C)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(ORG_NAME_D)
            is False
        )
        os.remove('/srv/app/feedback_config.json')

        # rating(ckan.ini)
        config.pop('ckan.feedback.resources.comment.rating.enable', None)
        config.pop('ckan.feedback.resources.comment.rating.enable_orgs', None)
        config.pop('ckan.feedback.resources.comment.rating.disable_orgs', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.comment.rating.enable', None) is None
        assert (
            config.get('ckan.feedback.resources.comment.rating.enable_orgs', None)
            is None
        )
        assert (
            config.get('ckan.feedback.resources.comment.rating.disable_orgs', None)
            is None
        )
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().resource_comment.rating.is_enable() is False
        assert FeedbackConfig().resource_comment.rating.is_enable(ORG_NAME_A) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(ORG_NAME_B) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(ORG_NAME_C) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(ORG_NAME_D) is False

        # rating(feedback_config.json)
        feedback_config = {"modules": {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.comment.rating.enable', None) is None
        assert (
            config.get('ckan.feedback.resources.comment.rating.enable_orgs', None)
            is None
        )
        assert (
            config.get('ckan.feedback.resources.comment.rating.disable_orgs', None)
            is None
        )
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.rating.is_enable() is False
        assert FeedbackConfig().resource_comment.rating.is_enable(ORG_NAME_A) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(ORG_NAME_B) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(ORG_NAME_C) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(ORG_NAME_D) is False
        os.remove('/srv/app/feedback_config.json')

        # image_attachment(ckan.ini)
        config.pop('ckan.feedback.resources.comment.image_attachment.enable', None)
        config.pop('ckan.feedback.resources.comment.image_attachment.enable_orgs', None)
        config.pop(
            'ckan.feedback.resources.comment.image_attachment.disable_orgs', None
        )

        FeedbackConfig().load_feedback_config()

        assert (
            config.get('ckan.feedback.resources.comment.image_attachment.enable', None)
            is None
        )
        assert (
            config.get(
                'ckan.feedback.resources.comment.image_attachment.enable_orgs', None
            )
            is None
        )
        assert (
            config.get(
                'ckan.feedback.resources.comment.image_attachment.disable_orgs', None
            )
            is None
        )
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().resource_comment.image_attachment.is_enable() is False
        assert (
            FeedbackConfig().resource_comment.image_attachment.is_enable(ORG_NAME_A)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.image_attachment.is_enable(ORG_NAME_B)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.image_attachment.is_enable(ORG_NAME_C)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.image_attachment.is_enable(ORG_NAME_D)
            is False
        )

        # image_attachment(feedback_config.json)
        feedback_config = {"modules": {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert (
            config.get('ckan.feedback.resources.comment.image_attachment.enable', None)
            is None
        )
        assert (
            config.get(
                'ckan.feedback.resources.comment.image_attachment.enable_orgs', None
            )
            is None
        )
        assert (
            config.get(
                'ckan.feedback.resources.comment.image_attachment.disable_orgs', None
            )
            is None
        )
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.image_attachment.is_enable() is False
        assert (
            FeedbackConfig().resource_comment.image_attachment.is_enable(ORG_NAME_A)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.image_attachment.is_enable(ORG_NAME_B)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.image_attachment.is_enable(ORG_NAME_C)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.image_attachment.is_enable(ORG_NAME_D)
            is False
        )
        os.remove('/srv/app/feedback_config.json')

        # downloads(ckan.ini)
        config.pop('ckan.feedback.downloads.enable', None)
        config.pop('ckan.feedback.downloads.enable_orgs', None)
        config.pop('ckan.feedback.downloads.disable_orgs', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.downloads.enable', None) is None
        assert config.get('ckan.feedback.downloads.enable_orgs', None) is None
        assert config.get('ckan.feedback.downloads.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().resource_comment.is_enable() is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is True

        # downloads(feedback_config.json)
        feedback_config = {"modules": {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.downloads.enable', None) is None
        assert config.get('ckan.feedback.downloads.enable_orgs', None) is None
        assert config.get('ckan.feedback.downloads.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_A) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_B) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_C) is True
        assert FeedbackConfig().resource_comment.is_enable(ORG_NAME_D) is True
        os.remove('/srv/app/feedback_config.json')

        # modal(ckan.ini)
        config.pop('ckan.feedback.download.modal.enable', None)
        config.pop('ckan.feedback.download.modal.enable_orgs', None)
        config.pop('ckan.feedback.download.modal.disable_orgs', None)
        FeedbackConfig().load_feedback_config()
        assert config.get('ckan.feedback.download.modal.enable', None) is None
        assert config.get('ckan.feedback.download.modal.enable_orgs', None) is None
        assert config.get('ckan.feedback.download.modal.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().download.modal.is_enable() is True
        assert FeedbackConfig().download.modal.is_enable(ORG_NAME_A) is True
        assert FeedbackConfig().download.modal.is_enable(ORG_NAME_B) is True
        assert FeedbackConfig().download.modal.is_enable(ORG_NAME_C) is True
        assert FeedbackConfig().download.modal.is_enable(ORG_NAME_D) is True
        # modal(feedback_config.json)
        feedback_config = {"modules": {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        FeedbackConfig().load_feedback_config()
        assert config.get('ckan.feedback.download.modal.enable', None) is None
        assert config.get('ckan.feedback.download.modal.enable_orgs', None) is None
        assert config.get('ckan.feedback.download.modal.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().download.modal.is_enable() is True
        assert FeedbackConfig().download.modal.is_enable(ORG_NAME_A) is True
        assert FeedbackConfig().download.modal.is_enable(ORG_NAME_B) is True
        assert FeedbackConfig().download.modal.is_enable(ORG_NAME_C) is True
        assert FeedbackConfig().download.modal.is_enable(ORG_NAME_D) is True
        os.remove('/srv/app/feedback_config.json')

        # likes(ckan.ini)
        config.pop('ckan.feedback.likes.enable', None)
        config.pop('ckan.feedback.likes.enable_orgs', None)
        config.pop('ckan.feedback.likes.disable_orgs', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.likes.enable', None) is None
        assert config.get('ckan.feedback.likes.enable_orgs', None) is None
        assert config.get('ckan.feedback.likes.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().like.is_enable() is True
        assert FeedbackConfig().like.is_enable(ORG_NAME_A) is True
        assert FeedbackConfig().like.is_enable(ORG_NAME_B) is True
        assert FeedbackConfig().like.is_enable(ORG_NAME_C) is True
        assert FeedbackConfig().like.is_enable(ORG_NAME_D) is True

        # likes(feedback_config.json)
        feedback_config = {"modules": {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.likes.enable', None) is None
        assert config.get('ckan.feedback.likes.enable_orgs', None) is None
        assert config.get('ckan.feedback.likes.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().like.is_enable() is True
        assert FeedbackConfig().like.is_enable(ORG_NAME_A) is True
        assert FeedbackConfig().like.is_enable(ORG_NAME_B) is True
        assert FeedbackConfig().like.is_enable(ORG_NAME_C) is True
        assert FeedbackConfig().like.is_enable(ORG_NAME_D) is True
        os.remove('/srv/app/feedback_config.json')

        # moral_keeper_ai(ckan.ini)
        config.pop('ckan.feedback.moral_keeper_ai.enable', None)
        config.pop('ckan.feedback.moral_keeper_ai.enable_orgs', None)
        config.pop('ckan.feedback.moral_keeper_ai.disable_orgs', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.moral_keeper_ai.enable', None) is None
        assert config.get('ckan.feedback.moral_keeper_ai.enable_orgs', None) is None
        assert config.get('ckan.feedback.moral_keeper_ai.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().moral_keeper_ai.is_enable() is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(ORG_NAME_A) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(ORG_NAME_B) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(ORG_NAME_C) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(ORG_NAME_D) is False

        # moral_keeper_ai(feedback_config.json)
        feedback_config = {"modules": {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.moral_keeper_ai.enable', None) is None
        assert config.get('ckan.feedback.moral_keeper_ai.enable_orgs', None) is None
        assert config.get('ckan.feedback.moral_keeper_ai.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().moral_keeper_ai.is_enable() is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(ORG_NAME_A) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(ORG_NAME_B) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(ORG_NAME_C) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(ORG_NAME_D) is False
        os.remove('/srv/app/feedback_config.json')

    def test_recaptcha_config(self):
        # without feedback_config_file and .ini file
        config.pop('ckan.feedback.recaptcha.enable', None)
        config.pop('ckan.feedback.recaptcha.publickey', None)
        config.pop('ckan.feedback.recaptcha.privatekey', None)
        config.pop('ckan.feedback.recaptcha.score_threshold', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.recaptcha.enable', 'None') == 'None'
        assert config.get('ckan.feedback.recaptcha.publickey', 'None') == 'None'
        assert config.get('ckan.feedback.recaptcha.privatekey', 'None') == 'None'
        assert config.get('ckan.feedback.recaptcha.score_threshold', 'None') == 'None'
        assert FeedbackConfig().is_feedback_config_file is False
        assert (
            FeedbackConfig().recaptcha.is_enable() is FeedbackConfig().recaptcha.default
        )
        assert (
            FeedbackConfig().recaptcha.publickey.get()
            is FeedbackConfig().recaptcha.publickey.default
        )
        assert (
            FeedbackConfig().recaptcha.privatekey.get()
            is FeedbackConfig().recaptcha.privatekey.default
        )
        assert (
            FeedbackConfig().recaptcha.score_threshold.get()
            is FeedbackConfig().recaptcha.score_threshold.default
        )

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.recaptcha.enable'] = True
        config.pop('ckan.feedback.recaptcha.publickey', None)
        config.pop('ckan.feedback.recaptcha.privatekey', None)
        config.pop('ckan.feedback.recaptcha.score_threshold', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.recaptcha.enable', 'None') is True
        assert config.get('ckan.feedback.recaptcha.publickey', 'None') == 'None'
        assert config.get('ckan.feedback.recaptcha.privatekey', 'None') == 'None'
        assert config.get('ckan.feedback.recaptcha.score_threshold', 'None') == 'None'
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().recaptcha.is_enable() is True
        assert (
            FeedbackConfig().recaptcha.publickey.get()
            is FeedbackConfig().recaptcha.publickey.default
        )
        assert (
            FeedbackConfig().recaptcha.privatekey.get()
            is FeedbackConfig().recaptcha.privatekey.default
        )
        assert (
            FeedbackConfig().recaptcha.score_threshold.get()
            is FeedbackConfig().recaptcha.score_threshold.default
        )

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.recaptcha.enable'] = False
        config.pop('ckan.feedback.recaptcha.publickey', None)
        config.pop('ckan.feedback.recaptcha.privatekey', None)
        config.pop('ckan.feedback.recaptcha.score_threshold', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.recaptcha.enable', 'None') is False
        assert config.get('ckan.feedback.recaptcha.publickey', 'None') == 'None'
        assert config.get('ckan.feedback.recaptcha.privatekey', 'None') == 'None'
        assert config.get('ckan.feedback.recaptcha.score_threshold', 'None') == 'None'
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().recaptcha.is_enable() is False
        assert (
            FeedbackConfig().recaptcha.publickey.get()
            is FeedbackConfig().recaptcha.publickey.default
        )
        assert (
            FeedbackConfig().recaptcha.privatekey.get()
            is FeedbackConfig().recaptcha.privatekey.default
        )
        assert (
            FeedbackConfig().recaptcha.score_threshold.get()
            is FeedbackConfig().recaptcha.score_threshold.default
        )

        # with feedback_config_file enable is False
        config['ckan.feedback.recaptcha.enable'] = True
        config.pop('ckan.feedback.recaptcha.publickey', None)
        config.pop('ckan.feedback.recaptcha.privatekey', None)
        config.pop('ckan.feedback.recaptcha.score_threshold', None)

        feedback_config = {
            'modules': {
                "recaptcha": {
                    "enable": False,
                },
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.recaptcha.enable', 'None') is False
        assert config.get('ckan.feedback.recaptcha.publickey', 'None') == 'None'
        assert config.get('ckan.feedback.recaptcha.privatekey', 'None') == 'None'
        assert config.get('ckan.feedback.recaptcha.score_threshold', 'None') == 'None'
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().recaptcha.is_enable() is False
        assert (
            FeedbackConfig().recaptcha.publickey.get()
            is FeedbackConfig().recaptcha.publickey.default
        )
        assert (
            FeedbackConfig().recaptcha.privatekey.get()
            is FeedbackConfig().recaptcha.privatekey.default
        )
        assert (
            FeedbackConfig().recaptcha.score_threshold.get()
            is FeedbackConfig().recaptcha.score_threshold.default
        )
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True
        config['ckan.feedback.notice.email.enable'] = False
        config.pop('ckan.feedback.notice.email.template_directory', None)
        config.pop('ckan.feedback.notice.email.template_utilization', None)
        config.pop('ckan.feedback.notice.email.template_utilization_comment', None)
        config.pop('ckan.feedback.notice.email.template_resource_comment', None)
        config.pop('ckan.feedback.notice.email.subject_utilization', None)
        config.pop('ckan.feedback.notice.email.subject_utilization_comment', None)
        config.pop('ckan.feedback.notice.email.subject_resource_comment', None)

        feedback_config = {
            'modules': {
                "recaptcha": {
                    "enable": True,
                    "publickey": "xxxxxxxxx",
                    "privatekey": "yyyyyyyy",
                    "score_threshold": 0.3,
                },
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.recaptcha.enable', 'None') is True
        assert config.get('ckan.feedback.recaptcha.publickey', 'None') == "xxxxxxxxx"
        assert config.get('ckan.feedback.recaptcha.privatekey', 'None') == "yyyyyyyy"
        assert config.get('ckan.feedback.recaptcha.score_threshold', 'None') == 0.3
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().recaptcha.is_enable() is True
        assert FeedbackConfig().recaptcha.publickey.get() == "xxxxxxxxx"
        assert FeedbackConfig().recaptcha.privatekey.get() == "yyyyyyyy"
        assert FeedbackConfig().recaptcha.score_threshold.get() == 0.3
        os.remove('/srv/app/feedback_config.json')

    def test_notice_email_config(self):
        # without feedback_config_file and .ini file
        config.pop('ckan.feedback.notice.email.enable', None)
        config.pop('ckan.feedback.notice.email.template_directory', None)
        config.pop('ckan.feedback.notice.email.template_utilization', None)
        config.pop('ckan.feedback.notice.email.template_utilization_comment', None)
        config.pop('ckan.feedback.notice.email.template_resource_comment', None)
        config.pop('ckan.feedback.notice.email.subject_utilization', None)
        config.pop('ckan.feedback.notice.email.subject_utilization_comment', None)
        config.pop('ckan.feedback.notice.email.subject_resource_comment', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.notice.email.enable', 'None') == 'None'
        assert (
            config.get('ckan.feedback.notice.email.template_directory', 'None')
            == 'None'
        )
        assert (
            config.get('ckan.feedback.notice.email.template_utilization', 'None')
            == 'None'
        )
        assert (
            config.get(
                'ckan.feedback.notice.email.template_utilization_comment', 'None'
            )
            == 'None'
        )
        assert (
            config.get('ckan.feedback.notice.email.template_resource_comment', 'None')
            == 'None'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization', 'None')
            == 'None'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization_comment', 'None')
            == 'None'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_resource_comment', 'None')
            == 'None'
        )
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().notice_email.is_enable() is False
        assert (
            FeedbackConfig().notice_email.template_directory.get()
            == FeedbackConfig().notice_email.template_directory.default
        )
        assert (
            FeedbackConfig().notice_email.template_utilization.get()
            == FeedbackConfig().notice_email.template_utilization.default
        )
        assert (
            FeedbackConfig().notice_email.template_utilization_comment.get()
            == FeedbackConfig().notice_email.template_utilization_comment.default
        )
        assert (
            FeedbackConfig().notice_email.template_resource_comment.get()
            == FeedbackConfig().notice_email.template_resource_comment.default
        )
        assert (
            FeedbackConfig().notice_email.subject_utilization.get()
            == FeedbackConfig().notice_email.subject_utilization.default
        )
        assert (
            FeedbackConfig().notice_email.subject_utilization_comment.get()
            == FeedbackConfig().notice_email.subject_utilization_comment.default
        )
        assert (
            FeedbackConfig().notice_email.subject_resource_comment.get()
            == FeedbackConfig().notice_email.subject_resource_comment.default
        )

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.notice.email.enable'] = True
        config['ckan.feedback.notice.email.template_directory'] = (
            'test_template_directory'
        )
        config['ckan.feedback.notice.email.template_utilization'] = (
            'test_template_utilization'
        )
        config['ckan.feedback.notice.email.template_utilization_comment'] = (
            'test_template_utilization_comment'
        )
        config['ckan.feedback.notice.email.template_resource_comment'] = (
            'test_template_resource_comment'
        )
        config['ckan.feedback.notice.email.subject_utilization'] = (
            'test_subject_utilization'
        )
        config['ckan.feedback.notice.email.subject_utilization_comment'] = (
            'test_subject_utilization_comment'
        )
        config['ckan.feedback.notice.email.subject_resource_comment'] = (
            'test_subject_resource_comment'
        )

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.notice.email.enable', 'None') is True
        assert (
            config.get('ckan.feedback.notice.email.template_directory', 'None')
            == 'test_template_directory'
        )
        assert (
            config.get('ckan.feedback.notice.email.template_utilization', 'None')
            == 'test_template_utilization'
        )
        assert (
            config.get(
                'ckan.feedback.notice.email.template_utilization_comment', 'None'
            )
            == 'test_template_utilization_comment'
        )
        assert (
            config.get('ckan.feedback.notice.email.template_resource_comment', 'None')
            == 'test_template_resource_comment'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization', 'None')
            == 'test_subject_utilization'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization_comment', 'None')
            == 'test_subject_utilization_comment'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_resource_comment', 'None')
            == 'test_subject_resource_comment'
        )
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().notice_email.is_enable() is True
        assert (
            FeedbackConfig().notice_email.template_directory.get()
            == 'test_template_directory'
        )
        assert (
            FeedbackConfig().notice_email.template_utilization.get()
            == 'test_template_utilization'
        )
        assert (
            FeedbackConfig().notice_email.template_utilization_comment.get()
            == 'test_template_utilization_comment'
        )
        assert (
            FeedbackConfig().notice_email.template_resource_comment.get()
            == 'test_template_resource_comment'
        )
        assert (
            FeedbackConfig().notice_email.subject_utilization.get()
            == 'test_subject_utilization'
        )
        assert (
            FeedbackConfig().notice_email.subject_utilization_comment.get()
            == 'test_subject_utilization_comment'
        )
        assert (
            FeedbackConfig().notice_email.subject_resource_comment.get()
            == 'test_subject_resource_comment'
        )

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.notice.email.enable'] = False
        config.pop('ckan.feedback.notice.email.template_directory', None)
        config.pop('ckan.feedback.notice.email.template_utilization', None)
        config.pop('ckan.feedback.notice.email.template_utilization_comment', None)
        config.pop('ckan.feedback.notice.email.template_resource_comment', None)
        config.pop('ckan.feedback.notice.email.subject_utilization', None)
        config.pop('ckan.feedback.notice.email.subject_utilization_comment', None)
        config.pop('ckan.feedback.notice.email.subject_resource_comment', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.notice.email.enable', 'None') is False
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().notice_email.is_enable() is False

        # with feedback_config_file enable is False
        config['ckan.feedback.notice.email.enable'] = True
        config.pop('ckan.feedback.notice.email.template_directory', None)
        config.pop('ckan.feedback.notice.email.template_utilization', None)
        config.pop('ckan.feedback.notice.email.template_utilization_comment', None)
        config.pop('ckan.feedback.notice.email.template_resource_comment', None)
        config.pop('ckan.feedback.notice.email.subject_utilization', None)
        config.pop('ckan.feedback.notice.email.subject_utilization_comment', None)
        config.pop('ckan.feedback.notice.email.subject_resource_comment', None)

        feedback_config = {
            'modules': {
                'notice': {
                    'email': {
                        'enable': False,
                    }
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.notice.email.enable', 'None') is False
        assert (
            config.get('ckan.feedback.notice.email.template_directory', 'None')
            == 'None'
        )
        assert (
            config.get('ckan.feedback.notice.email.template_utilization', 'None')
            == 'None'
        )
        assert (
            config.get(
                'ckan.feedback.notice.email.template_utilization_comment', 'None'
            )
            == 'None'
        )
        assert (
            config.get('ckan.feedback.notice.email.template_resource_comment', 'None')
            == 'None'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization', 'None')
            == 'None'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization_comment', 'None')
            == 'None'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_resource_comment', 'None')
            == 'None'
        )
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().notice_email.is_enable() is False
        assert (
            FeedbackConfig().notice_email.template_directory.get()
            == FeedbackConfig().notice_email.template_directory.default
        )
        assert (
            FeedbackConfig().notice_email.template_utilization.get()
            == FeedbackConfig().notice_email.template_utilization.default
        )
        assert (
            FeedbackConfig().notice_email.template_utilization_comment.get()
            == FeedbackConfig().notice_email.template_utilization_comment.default
        )
        assert (
            FeedbackConfig().notice_email.template_resource_comment.get()
            == FeedbackConfig().notice_email.template_resource_comment.default
        )
        assert (
            FeedbackConfig().notice_email.subject_utilization.get()
            == FeedbackConfig().notice_email.subject_utilization.default
        )
        assert (
            FeedbackConfig().notice_email.subject_utilization_comment.get()
            == FeedbackConfig().notice_email.subject_utilization_comment.default
        )
        assert (
            FeedbackConfig().notice_email.subject_resource_comment.get()
            == FeedbackConfig().notice_email.subject_resource_comment.default
        )
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True
        config['ckan.feedback.notice.email.enable'] = False
        config.pop('ckan.feedback.notice.email.template_directory', None)
        config.pop('ckan.feedback.notice.email.template_utilization', None)
        config.pop('ckan.feedback.notice.email.template_utilization_comment', None)
        config.pop('ckan.feedback.notice.email.template_resource_comment', None)
        config.pop('ckan.feedback.notice.email.subject_utilization', None)
        config.pop('ckan.feedback.notice.email.subject_utilization_comment', None)
        config.pop('ckan.feedback.notice.email.subject_resource_comment', None)

        feedback_config = {
            'modules': {
                'notice': {
                    'email': {
                        'enable': True,
                        'template_directory': 'test_template_directory',
                        'template_utilization': 'test_template_utilization',
                        'template_utilization_comment': (
                            'test_template_utilization_comment'
                        ),
                        'template_resource_comment': 'test_template_resource_comment',
                        'subject_utilization': 'test_subject_utilization',
                        'subject_utilization_comment': (
                            'test_subject_utilization_comment'
                        ),
                        'subject_resource_comment': 'test_subject_resource_comment',
                    }
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.notice.email.enable', 'None') is True
        assert (
            config.get('ckan.feedback.notice.email.template_directory', 'None')
            == 'test_template_directory'
        )
        assert (
            config.get('ckan.feedback.notice.email.template_utilization', 'None')
            == 'test_template_utilization'
        )
        assert (
            config.get(
                'ckan.feedback.notice.email.template_utilization_comment', 'None'
            )
            == 'test_template_utilization_comment'
        )
        assert (
            config.get('ckan.feedback.notice.email.template_resource_comment', 'None')
            == 'test_template_resource_comment'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization', 'None')
            == 'test_subject_utilization'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization_comment', 'None')
            == 'test_subject_utilization_comment'
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_resource_comment', 'None')
            == 'test_subject_resource_comment'
        )
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().notice_email.is_enable() is True
        assert (
            FeedbackConfig().notice_email.template_directory.get()
            == 'test_template_directory'
        )
        assert (
            FeedbackConfig().notice_email.template_utilization.get()
            == 'test_template_utilization'
        )
        assert (
            FeedbackConfig().notice_email.template_utilization_comment.get()
            == 'test_template_utilization_comment'
        )
        assert (
            FeedbackConfig().notice_email.template_resource_comment.get()
            == 'test_template_resource_comment'
        )
        assert (
            FeedbackConfig().notice_email.subject_utilization.get()
            == 'test_subject_utilization'
        )
        assert (
            FeedbackConfig().notice_email.subject_utilization_comment.get()
            == 'test_subject_utilization_comment'
        )
        assert (
            FeedbackConfig().notice_email.subject_resource_comment.get()
            == 'test_subject_resource_comment'
        )
        os.remove('/srv/app/feedback_config.json')

    def test_get_enable_org_names_with_enable_is_False(self):
        feedback_config = {"modules": {"resources": {"enable": False}}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        result = FeedbackConfig().resource_comment.get_enable_org_names()

        assert result == []

        os.remove('/srv/app/feedback_config.json')

    @patch('ckanext.feedback.services.common.config.organization_service')
    def test_get_enable_org_names_with_disable_orgs(self, mock_organization_service):
        feedback_config = {
            "modules": {
                "resources": {"enable": True, "disable_orgs": [ORG_NAME_A, ORG_NAME_B]}
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        mock_organization_service.get_organization_name_list.return_value = [
            ORG_NAME_A,
            ORG_NAME_B,
            ORG_NAME_C,
            ORG_NAME_D,
        ]

        result = FeedbackConfig().resource_comment.get_enable_org_names()

        assert result == [ORG_NAME_C, ORG_NAME_D]

        os.remove('/srv/app/feedback_config.json')

    @patch('ckanext.feedback.services.common.config.organization_service')
    def test_get_enable_org_names_with_enable_orgs(self, mock_organization_service):
        feedback_config = {
            "modules": {
                "resources": {"enable": True, "enable_orgs": [ORG_NAME_A, ORG_NAME_B]}
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        mock_organization_service.get_organization_name_list.return_value = [
            ORG_NAME_A,
            ORG_NAME_B,
            ORG_NAME_C,
            ORG_NAME_D,
        ]

        result = FeedbackConfig().resource_comment.get_enable_org_names()

        assert result == [ORG_NAME_A, ORG_NAME_B]

        os.remove('/srv/app/feedback_config.json')

    @patch('ckanext.feedback.services.common.config.organization_service')
    def test_get_enable_org_names_with_enable_orgs_and_disable_orgs(
        self, mock_organization_service
    ):
        feedback_config = {"modules": {"resources": {"enable": True}}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        mock_organization_service.get_organization_name_list.return_value = [
            ORG_NAME_A,
            ORG_NAME_B,
            ORG_NAME_C,
            ORG_NAME_D,
        ]

        result = FeedbackConfig().resource_comment.get_enable_org_names()

        assert result == [ORG_NAME_A, ORG_NAME_B, ORG_NAME_C, ORG_NAME_D]

        os.remove('/srv/app/feedback_config.json')

    def test_set_enable_and_enable_orgs_and_disable_orgs_with_module_config(self):
        from ckan.common import config

        from ckanext.feedback.services.common.config import DownloadsConfig

        config.pop('ckan.feedback.downloads.enable', None)
        config.pop('ckan.feedback.downloads.enable_orgs', None)
        config.pop('ckan.feedback.downloads.disable_orgs', None)

        module_config = {
            "enable": True,
            "enable_orgs": ["org-a", "org-b"],
            "disable_orgs": ["org-c"],
        }

        downloads_config = DownloadsConfig()
        downloads_config.set_enable_and_enable_orgs_and_disable_orgs(module_config)

        assert config.get('ckan.feedback.downloads.enable') is True
        assert config.get('ckan.feedback.downloads.enable_orgs') == ["org-a", "org-b"]
        assert config.get('ckan.feedback.downloads.disable_orgs') == ["org-c"]

    def test_set_enable_and_enable_orgs_and_disable_orgs_with_none(self):
        from ckan.common import config

        from ckanext.feedback.services.common.config import DownloadsConfig

        config['ckan.feedback.downloads.enable'] = True
        config['ckan.feedback.downloads.enable_orgs'] = ["org-a"]
        config['ckan.feedback.downloads.disable_orgs'] = ["org-b"]

        downloads_config = DownloadsConfig()
        downloads_config.set_enable_and_enable_orgs_and_disable_orgs(None)

        assert config.get('ckan.feedback.downloads.enable') is None
        assert config.get('ckan.feedback.downloads.enable_orgs') is None
        assert config.get('ckan.feedback.downloads.disable_orgs') is None

    def test_set_enable_and_enable_orgs_and_disable_orgs_partial_fields(self):
        from ckan.common import config

        from ckanext.feedback.services.common.config import DownloadsConfig

        config.pop('ckan.feedback.downloads.enable', None)
        config.pop('ckan.feedback.downloads.enable_orgs', None)
        config.pop('ckan.feedback.downloads.disable_orgs', None)

        module_config = {"enable": False}

        downloads_config = DownloadsConfig()
        downloads_config.set_enable_and_enable_orgs_and_disable_orgs(module_config)

        assert config.get('ckan.feedback.downloads.enable') is False
        assert config.get('ckan.feedback.downloads.enable_orgs') is None
        assert config.get('ckan.feedback.downloads.disable_orgs') is None

    def test_downloads_config_load_config_with_full_config(self):
        from ckan.common import config

        from ckanext.feedback.services.common.config import DownloadsConfig

        feedback_config = {
            "modules": {
                "downloads": {
                    "enable": True,
                    "enable_orgs": ["org-a"],
                    "feedback_prompt": {
                        "modal": {"enable": False, "disable_orgs": ["org-b"]}
                    },
                }
            }
        }

        download_config = DownloadsConfig()
        download_config.load_config(feedback_config)

        assert config.get('ckan.feedback.downloads.enable') is True
        assert config.get('ckan.feedback.downloads.enable_orgs') == ["org-a"]
        assert (
            config.get('ckan.feedback.downloads.feedback_prompt.modal.enable') is False
        )
        assert config.get(
            'ckan.feedback.downloads.feedback_prompt.modal.disable_orgs'
        ) == ["org-b"]

    def test_download_config_load_config_missing_download_module(self):
        from ckan.common import config

        from ckanext.feedback.services.common.config import DownloadsConfig

        config.pop('ckan.feedback.downloads.enable', None)
        config.pop('ckan.feedback.downloads.enable_orgs', None)

        feedback_config = {"modules": {}}

        downloads_config = DownloadsConfig()
        downloads_config.load_config(feedback_config)

        assert config.get('ckan.feedback.downloads.enable') is None
        assert config.get('ckan.feedback.downloads.enable_orgs') is None

    @patch('ckanext.feedback.services.common.config.toolkit')
    def test_set_config_no_error_when_config_missing(self, mock_toolkit):
        feedback_config = {
            'modules': {
                'downloads': {'enable': True},
                'resources': {'enable': True},
                'utilizations': {'enable': True},
                'likes': {'enable': True},
            }
        }

        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        mock_toolkit.error_shout.assert_not_called()

        os.remove('/srv/app/feedback_config.json')

    def test_set_config_uses_ckan_ini_when_feedback_config_missing(self):
        config['ckan.feedback.recaptcha.enable'] = True
        config['ckan.feedback.recaptcha.privatekey'] = 'test_private_key'
        config['ckan.feedback.recaptcha.publickey'] = 'test_public_key'
        config['ckan.feedback.recaptcha.score_threshold'] = 0.5

        feedback_config = {'modules': {}}

        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.recaptcha.enable') is True
        assert FeedbackConfig().recaptcha.privatekey.get() == 'test_private_key'
        assert FeedbackConfig().recaptcha.publickey.get() == 'test_public_key'
        assert FeedbackConfig().recaptcha.score_threshold.get() == 0.5

        config.pop('ckan.feedback.recaptcha.enable', None)
        config.pop('ckan.feedback.recaptcha.privatekey', None)
        config.pop('ckan.feedback.recaptcha.publickey', None)
        config.pop('ckan.feedback.recaptcha.score_threshold', None)
        os.remove('/srv/app/feedback_config.json')

    def test_set_config_uses_default_when_no_config_exists(self):
        config.pop('ckan.feedback.recaptcha.enable', None)
        config.pop('ckan.feedback.recaptcha.privatekey', None)
        config.pop('ckan.feedback.recaptcha.publickey', None)
        config.pop('ckan.feedback.recaptcha.score_threshold', None)
        config.pop('ckan.feedback.recaptcha.force_all', None)
        config.pop('ckan.feedback.notice.email.enable', None)
        config.pop('ckan.feedback.notice.email.template_directory', None)

        feedback_config = {'modules': {}}

        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert FeedbackConfig().recaptcha.privatekey.get() == ''
        assert FeedbackConfig().recaptcha.publickey.get() == ''
        assert FeedbackConfig().recaptcha.score_threshold.get() == 0.5
        assert FeedbackConfig().recaptcha.force_all.get() is False

        default_template_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                '..',
                'templates',
                'email_notification',
            )
        )
        assert (
            FeedbackConfig().notice_email.template_directory.get()
            == default_template_dir
        )

        os.remove('/srv/app/feedback_config.json')
