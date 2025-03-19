import json
import os
from types import SimpleNamespace
from unittest.mock import patch

import ckan.tests.factories as factories
import pytest
from ckan import model
from ckan.common import config
from ckan.plugins import toolkit
from ckan.plugins.toolkit import ValidationError

from ckanext.feedback.command import feedback
from ckanext.feedback.plugin import FeedbackPlugin
from ckanext.feedback.services.common.config import (
    CONFIG_HANDLER_PATH,
    FeedbackConfig,
    download_handler,
    get_organization,
)

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestCheck:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()

    def test_check_administrator(self):
        enable_org = factories.Organization(
            is_organization=True,
            name='enable_org',
            type='organization',
            title='enable_org',
        )

        result = get_organization(enable_org['id'])
        assert result.name == enable_org['name']

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
    @patch('ckanext.feedback.services.common.config.ReCaptchaConfig.load_config')
    @patch('ckanext.feedback.services.common.config.NoticeEmailConfig.load_config')
    def test_load_feedback_config_with_feedback_config_file(
        self,
        mock_DownloadsConfig_load_config,
        mock_ResourceCommentConfig_load_config,
        mock_UtilizationConfig_load_config,
        mock_ReCaptchaConfig_load_config,
        mock_NoticeEmailConfig_load_config,
    ):
        # without feedback_config_file and .ini file
        try:
            os.remove('/srv/app/feedback_config.json')
        except FileNotFoundError:
            pass

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
        mock_toolkit.error_shout.call_count == 4
        os.remove('/srv/app/feedback_config.json')

    @patch('ckanext.feedback.services.common.config.toolkit')
    def test_update_config_json_decode_error(self, mock_toolkit):
        with open('/srv/app/feedback_config.json', 'w') as f:
            f.write('{"modules":')

        FeedbackConfig().load_feedback_config()
        mock_toolkit.error_shout.assert_called_once_with(
            'The feedback config file not decoded correctly'
        )
        os.remove('/srv/app/feedback_config.json')

    def test_get_commands(self):
        result = FeedbackPlugin.get_commands(self)
        assert result == [feedback.feedback]

    @patch('ckanext.feedback.services.common.config.get_organization')
    def test_load_feedback_config_and_is_enable(self, mock_get_organization):
        org_name_a = 'org-name-a'
        org_name_b = 'org-name-b'
        org_name_c = 'org-name-c'
        org_name_d = 'org-name-d'

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
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is True

        # Write enable = True in ckan.ini
        config['ckan.feedback.resources.enable'] = True

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) is None
        assert config.get('ckan.feedback.resources.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().resource_comment.is_enable() is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is True

        # Write enable = False in ckan.ini
        config['ckan.feedback.resources.enable'] = False

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is False
        assert config.get('ckan.feedback.resources.enable_orgs', None) is None
        assert config.get('ckan.feedback.resources.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().resource_comment.is_enable() is False
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is False
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is False
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is False
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is False

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
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_a})
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_b})
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_c})
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_d})
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is True
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
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_a})
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_b})
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_c})
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_d})
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is True
        os.remove('/srv/app/feedback_config.json')

        # The "enable_orgs" key is listed in feedback_config.json
        config.pop('ckan.feedback.resources.enable', None)

        feedback_config = {
            "modules": {
                "resources": {"enable": True, "enable_orgs": [org_name_a, org_name_b]}
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) == [
            org_name_a,
            org_name_b,
        ]
        assert config.get('ckan.feedback.resources.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_a})
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_b})
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_c})
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is False
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_d})
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is False
        os.remove('/srv/app/feedback_config.json')

        # The "disable_orgs" key is listed in feedback_config.json
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.enable_orgs', None)

        feedback_config = {
            "modules": {
                "resources": {"enable": True, "disable_orgs": [org_name_a, org_name_b]}
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) is None
        assert config.get('ckan.feedback.resources.disable_orgs', None) == [
            org_name_a,
            org_name_b,
        ]
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_a})
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is False
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_b})
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is False
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_c})
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_d})
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is True
        os.remove('/srv/app/feedback_config.json')

        # Both "enable_orgs" and "disable_orgs" are listed in feedback_config.json
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.disable_orgs', None)

        feedback_config = {
            "modules": {
                "resources": {
                    "enable": True,
                    "enable_orgs": [org_name_a, org_name_b],
                    "disable_orgs": [org_name_c],
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) == [
            org_name_a,
            org_name_b,
        ]
        assert config.get('ckan.feedback.resources.disable_orgs', None) == [org_name_c]
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_a})
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_b})
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_c})
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is False
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_d})
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is True
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
                    "enable_orgs": [org_name_a, org_name_b],
                    "disable_orgs": [org_name_a],
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.resources.enable', None) is True
        assert config.get('ckan.feedback.resources.enable_orgs', None) == [
            org_name_a,
            org_name_b,
        ]
        assert config.get('ckan.feedback.resources.disable_orgs', None) == [org_name_a]
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().resource_comment.is_enable() is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_a})
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is False
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_b})
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_c})
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is True
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_d})
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is True
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
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_a})
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is False
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_b})
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is False
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_c})
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is False
        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_d})
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is False
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
        mock_get_organization.return_value = None
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is False
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is False
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is False
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is False
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

        assert error_message == (
            "The configuration of the \"resources\" module "
            "in \"feedback_config.json\" is incomplete. "
            "Please specify the \"enable\" key "
            "(e.g., {\"modules\": {\"resources\": {\"enable\": true}}})."
        )
        os.remove('/srv/app/feedback_config.json')

        # The value of "enable_orgs" is not an array of strings
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.enable_orgs', None)
        config.pop('ckan.feedback.resources.disable_orgs', None)

        feedback_config = {
            "modules": {"resources": {"enable": True, "enable_orgs": org_name_a}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_a})

        with pytest.raises(ValidationError) as exc_info:
            FeedbackConfig().resource_comment.is_enable(org_name_a)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == (
            "The \"enable_orgs\" key must be a string array "
            "to specify valid organizations "
            "(e.g., \"enable_orgs\": [\"org-name-a\", \"org-name-b\"])."
        )
        os.remove('/srv/app/feedback_config.json')

        # The value of "disable_orgs" is not an array of strings
        config.pop('ckan.feedback.resources.enable', None)
        config.pop('ckan.feedback.resources.enable_orgs', None)
        config.pop('ckan.feedback.resources.disable_orgs', None)

        feedback_config = {
            "modules": {"resources": {"enable": True, "disable_orgs": org_name_a}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        mock_get_organization.return_value = SimpleNamespace(**{'name': org_name_a})

        with pytest.raises(ValidationError) as exc_info:
            FeedbackConfig().resource_comment.is_enable(org_name_a)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "The \"disable_orgs\" key must be a string array "
            "to specify invalid organizations "
            "(e.g., \"disable_orgs\": [\"org-name-a\", \"org-name-b\"])."
        )
        os.remove('/srv/app/feedback_config.json')

    @patch('ckanext.feedback.services.common.config.get_organization')
    def test_module_default_config(self, mock_get_organization):
        org_name_a = 'org-name-a'
        org_name_b = 'org-name-b'
        org_name_c = 'org-name-c'
        org_name_d = 'org-name-d'

        # utilization(ckan.ini)
        config.pop('ckan.feedback.utilization.enable', None)
        config.pop('ckan.feedback.utilization.enable_orgs', None)
        config.pop('ckan.feedback.utilization.disable_orgs', None)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.utilization.enable', None) is None
        assert config.get('ckan.feedback.utilization.enable_orgs', None) is None
        assert config.get('ckan.feedback.utilization.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is False
        assert FeedbackConfig().utilization.is_enable() is True
        assert FeedbackConfig().utilization.is_enable(org_name_a) is True
        assert FeedbackConfig().utilization.is_enable(org_name_b) is True
        assert FeedbackConfig().utilization.is_enable(org_name_c) is True
        assert FeedbackConfig().utilization.is_enable(org_name_d) is True

        # utilization(feedback_config.json)
        feedback_config = {"modules": {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        FeedbackConfig().load_feedback_config()

        assert config.get('ckan.feedback.utilization.enable', None) is None
        assert config.get('ckan.feedback.utilization.enable_orgs', None) is None
        assert config.get('ckan.feedback.utilization.disable_orgs', None) is None
        assert FeedbackConfig().is_feedback_config_file is True
        assert FeedbackConfig().utilization.is_enable() is True
        assert FeedbackConfig().utilization.is_enable(org_name_a) is True
        assert FeedbackConfig().utilization.is_enable(org_name_b) is True
        assert FeedbackConfig().utilization.is_enable(org_name_c) is True
        assert FeedbackConfig().utilization.is_enable(org_name_d) is True
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
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(org_name_a)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(org_name_b)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(org_name_c)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(org_name_d)
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
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(org_name_a)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(org_name_b)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(org_name_c)
            is False
        )
        assert (
            FeedbackConfig().resource_comment.repeat_post_limit.is_enable(org_name_d)
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
        assert FeedbackConfig().resource_comment.rating.is_enable(org_name_a) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(org_name_b) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(org_name_c) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(org_name_d) is False

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
        assert FeedbackConfig().resource_comment.rating.is_enable(org_name_a) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(org_name_b) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(org_name_c) is False
        assert FeedbackConfig().resource_comment.rating.is_enable(org_name_d) is False
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
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is True

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
        assert FeedbackConfig().resource_comment.is_enable(org_name_a) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_b) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_c) is True
        assert FeedbackConfig().resource_comment.is_enable(org_name_d) is True
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
        assert FeedbackConfig().like.is_enable(org_name_a) is True
        assert FeedbackConfig().like.is_enable(org_name_b) is True
        assert FeedbackConfig().like.is_enable(org_name_c) is True
        assert FeedbackConfig().like.is_enable(org_name_d) is True

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
        assert FeedbackConfig().like.is_enable(org_name_a) is True
        assert FeedbackConfig().like.is_enable(org_name_b) is True
        assert FeedbackConfig().like.is_enable(org_name_c) is True
        assert FeedbackConfig().like.is_enable(org_name_d) is True
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
        assert FeedbackConfig().moral_keeper_ai.is_enable(org_name_a) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(org_name_b) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(org_name_c) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(org_name_d) is False

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
        assert FeedbackConfig().moral_keeper_ai.is_enable(org_name_a) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(org_name_b) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(org_name_c) is False
        assert FeedbackConfig().moral_keeper_ai.is_enable(org_name_d) is False
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

    def test_get_enable_orgs(self):
        org_name_a = 'org-name-a'
        org_name_b = 'org-name-b'

        config['ckan.feedback.resources.enable'] = True
        config['ckan.feedback.resources.enable_orgs'] = [org_name_a, org_name_b]

        result = FeedbackConfig().resource_comment.get_enable_orgs()
        assert result == [org_name_a, org_name_b]

        config['ckan.feedback.resources.enable'] = False

        result = FeedbackConfig().resource_comment.get_enable_orgs()
        assert result is False
