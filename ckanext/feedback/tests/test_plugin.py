import json
import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from ckan import model
from ckan.common import _, config
from ckan.tests import factories

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

    def teardown_method(self, method):
        if os.path.isfile('/srv/app/feedback_config.json'):
            os.remove('/srv/app/feedback_config.json')

    def test_update_config_with_feedback_config_file(self):
        instance = FeedbackPlugin()

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_feedback_config_file is False

        # without .ini file
        feedback_config = {
            'modules': {
                'utilizations': {'enable': True, 'enable_orgs': []},
                'resources': {
                    'enable': True,
                    'enable_orgs': [],
                    'comments': {
                        'repeat_post_limit': {'enable': False, 'enable_orgs': []},
                        'rating': {'enable': False, 'enable_orgs': []},
                    },
                },
                'downloads': {
                    'enable': True,
                    'enable_orgs': [],
                },
                "notice": {
                    "email": {
                        "enable": True,
                        "template_directory": "/opt/ckan/default/src/ckanext-feedback/"
                        "ckanext/feedback/templates/email_notification",
                        "template_utilization": "utilization.text",
                        "template_utilization_comment": "utilization_comment.text",
                        "template_resource_comment": "resource_comment.text",
                        "subject_utilization": "Post a Utilization",
                        "subject_utilization_comment": "Post a Utilization comment",
                        "subject_resource_comment": "Post a Resource comment",
                    }
                },
                "recaptcha": {
                    "enable": True,
                    "publickey": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "privatekey": "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
                    "score_threshold": 0.5,
                },
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        instance.update_config(config)
        assert instance.is_feedback_config_file is True
        assert config.get('ckan.feedback.utilizations.enable') is True
        assert config.get('ckan.feedback.utilizations.enable_orgs') == []
        assert config.get('ckan.feedback.resources.enable') is True
        assert config.get('ckan.feedback.resources.enable_orgs') == []
        assert (
            config.get('ckan.feedback.resources.comment.repeat_post_limit.enable')
            is False
        )
        assert (
            config.get('ckan.feedback.resources.comment.repeat_post_limit.enable_orgs')
            == []
        )
        assert config.get('ckan.feedback.resources.comment.rating.enable') is False
        assert config.get('ckan.feedback.resources.comment.rating.enable_orgs') == []
        assert config.get('ckan.feedback.downloads.enable') is True
        assert config.get('ckan.feedback.downloads.enable_orgs') == []
        assert config.get('ckan.feedback.notice.email.enable') is True
        assert (
            config.get('ckan.feedback.notice.email.template_directory')
            == "/opt/ckan/default/src/ckanext-feedback/"
            "ckanext/feedback/templates/email_notification"
        )
        assert (
            config.get('ckan.feedback.notice.email.template_utilization')
            == "utilization.text"
        )
        assert (
            config.get('ckan.feedback.notice.email.template_utilization_comment')
            == "utilization_comment.text"
        )
        assert (
            config.get('ckan.feedback.notice.email.template_resource_comment')
            == "resource_comment.text"
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization')
            == "Post a Utilization"
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization_comment')
            == "Post a Utilization comment"
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_resource_comment')
            == "Post a Resource comment"
        )
        assert config.get('ckan.feedback.recaptcha.enable') is True
        assert (
            config.get('ckan.feedback.recaptcha.publickey')
            == "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        )
        assert (
            config.get('ckan.feedback.recaptcha.privatekey')
            == "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
        )
        assert config.get('ckan.feedback.recaptcha.score_threshold') == 0.5

        # with .ini file enable is opposite from feedback_config.json
        config['ckan.feedback.utilizations.enable'] = False
        config['ckan.feedback.resources.enable'] = False
        config['ckan.feedback.downloads.enable'] = False
        config['ckan.feedback.resources.comment.repeat_post_limit.enable'] = True
        config['ckan.feedback.resources.comment.rating.enable'] = True
        config['ckan.feedback.notice.email.enable'] = True
        config['ckan.feedback.notice.email.template_directory'] = ''
        config['ckan.feedback.notice.email.template_utilization'] = ''
        config['ckan.feedback.notice.email.template_utilization_comment'] = ''
        config['ckan.feedback.notice.email.template_resource_comment'] = ''
        config['ckan.feedback.notice.email.subject_utilization'] = ''
        config['ckan.feedback.notice.email.subject_utilization_comment'] = ''
        config['ckan.feedback.notice.email.subject_resource_comment'] = ''
        config['ckan.feedback.recaptcha.enable'] = True
        config['ckan.feedback.recaptcha.publickey'] = ''
        config['ckan.feedback.recaptcha.privatekey'] = ''
        config['ckan.feedback.recaptcha.score_threshold'] = ''
        instance.update_config(config)
        assert instance.is_feedback_config_file is True
        assert config.get('ckan.feedback.utilizations.enable') is True
        assert config.get('ckan.feedback.resources.enable') is True
        assert (
            config.get('ckan.feedback.resources.comment.repeat_post_limit.enable')
            is False
        )
        assert config.get('ckan.feedback.resources.comment.rating.enable') is False
        assert config.get('ckan.feedback.downloads.enable') is True
        assert config.get('ckan.feedback.notice.email.enable') is True
        assert (
            config.get('ckan.feedback.notice.email.template_directory')
            == "/opt/ckan/default/src/ckanext-feedback/"
            "ckanext/feedback/templates/email_notification"
        )
        assert (
            config.get('ckan.feedback.notice.email.template_utilization')
            == "utilization.text"
        )
        assert (
            config.get('ckan.feedback.notice.email.template_utilization_comment')
            == "utilization_comment.text"
        )
        assert (
            config.get('ckan.feedback.notice.email.template_resource_comment')
            == "resource_comment.text"
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization')
            == "Post a Utilization"
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_utilization_comment')
            == "Post a Utilization comment"
        )
        assert (
            config.get('ckan.feedback.notice.email.subject_resource_comment')
            == "Post a Resource comment"
        )
        assert config.get('ckan.feedback.recaptcha.enable') is True
        assert (
            config.get('ckan.feedback.recaptcha.publickey')
            == "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        )
        assert (
            config.get('ckan.feedback.recaptcha.privatekey')
            == "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
        )
        assert config.get('ckan.feedback.recaptcha.score_threshold') == 0.5

    @patch('ckanext.feedback.plugin.toolkit')
    def test_update_config_attribute_error(self, mock_toolkit):
        instance = FeedbackPlugin()
        feedback_config = {'modules': {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        instance.update_config(config)
        mock_toolkit.error_shout.call_count == 4

    @patch('ckanext.feedback.plugin.toolkit')
    def test_update_config_json_decode_error(self, mock_toolkit):
        instance = FeedbackPlugin()
        with open('/srv/app/feedback_config.json', 'w') as f:
            f.write('{"modules":')

        instance.update_config(config)
        mock_toolkit.error_shout.assert_called_once_with(
            'The feedback config file not decoded correctly'
        )

    def test_get_commands(self):
        result = FeedbackPlugin.get_commands(self)
        assert result == [feedback.feedback]

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
    ):
        instance = FeedbackPlugin()

        config['ckan.feedback.utilizations.enable'] = True
        config['ckan.feedback.resources.enable'] = True
        config['ckan.feedback.downloads.enable'] = True
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

        config['ckan.feedback.utilizations.enable'] = False
        config['ckan.feedback.resources.enable'] = False
        config['ckan.feedback.downloads.enable'] = False
        expected_blueprints = ['management_bp']
        actual_blueprints = instance.get_blueprint()

        assert actual_blueprints == expected_blueprints

    @patch('ckanext.feedback.plugin.feedback_config')
    def test_is_enabled_downloads_org(self, mock_feedback_config):
        instance = FeedbackPlugin()
        org_name = 'example_org_name'

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_downloads_org(org_name) is True

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.downloads.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_downloads_org(org_name) is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.downloads.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_downloads_org(org_name) is False

        # with feedback_config_file enable is False and org_name is not in enable_orgs
        feedback_config = {
            'modules': {'downloads': {'enable': False, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = None
        assert instance.is_enabled_downloads_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is False and org_name is in enable_orgs
        feedback_config = {
            'modules': {'downloads': {'enable': False, 'enable_orgs': [org_name]}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = SimpleNamespace(
            **{'name': org_name}
        )
        assert instance.is_enabled_downloads_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True and org_name is not in enable_orgs
        feedback_config = {
            'modules': {'downloads': {'enable': True, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = None
        assert instance.is_enabled_downloads_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True and org_name is in enable_orgs
        feedback_config = {
            'modules': {'downloads': {'enable': True, 'enable_orgs': [org_name]}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = SimpleNamespace(
            **{'name': org_name}
        )
        assert instance.is_enabled_downloads_org(org_name) is True
        os.remove('/srv/app/feedback_config.json')

    def test_is_enabled_downloads(self):
        instance = FeedbackPlugin()

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_downloads() is True

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.downloads.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_downloads() is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.downloads.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_downloads() is False

        # with feedback_config_file enable is False
        feedback_config = {
            'modules': {'downloads': {'enable': False, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_downloads() is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True
        feedback_config = {
            'modules': {'downloads': {'enable': True, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_downloads() is True

    @patch('ckanext.feedback.plugin.feedback_config')
    def test_is_enabled_resources_org(self, mock_feedback_config):
        instance = FeedbackPlugin()
        org_name = 'example_org_name'

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_resources_org(org_name) is True

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.resources.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_resources_org(org_name) is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.resources.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_resources_org(org_name) is False

        # with feedback_config_file enable is False and org_name is not in enable_orgs
        feedback_config = {
            'modules': {'resources': {'enable': False, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = None
        assert instance.is_enabled_resources_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is False and org_name is in enable_orgs
        feedback_config = {
            'modules': {'resources': {'enable': False, 'enable_orgs': [org_name]}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = SimpleNamespace(
            **{'name': org_name}
        )
        assert instance.is_enabled_resources_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True and org_name is not in enable_orgs
        feedback_config = {
            'modules': {'resources': {'enable': True, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = None
        assert instance.is_enabled_resources_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True and org
        feedback_config = {
            'modules': {'resources': {'enable': True, 'enable_orgs': [org_name]}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = SimpleNamespace(
            **{'name': org_name}
        )
        assert instance.is_enabled_resources_org(org_name) is True

    def test_is_enabled_resources(self):
        instance = FeedbackPlugin()

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_resources() is True

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.resources.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_resources() is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.resources.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_resources() is False

        # with feedback_config_file enable is False
        feedback_config = {
            'modules': {'resources': {'enable': False, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_resources() is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True
        feedback_config = {
            'modules': {'resources': {'enable': True, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_resources() is True

    @patch('ckanext.feedback.plugin.feedback_config')
    def test_is_enabled_utilizations_org(self, mock_feedback_config):
        instance = FeedbackPlugin()
        org_name = 'example_org_name'

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_utilizations_org(org_name) is True

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.utilizations.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_utilizations_org(org_name) is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.utilizations.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_utilizations_org(org_name) is False

        # with feedback_config_file enable is False and org_name is not in enable_orgs
        feedback_config = {
            'modules': {'utilizations': {'enable': False, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = None
        assert instance.is_enabled_utilizations_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is False and org_name is in enable_orgs
        feedback_config = {
            'modules': {'utilizations': {'enable': False, 'enable_orgs': [org_name]}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = SimpleNamespace(
            **{'name': org_name}
        )
        assert instance.is_enabled_utilizations_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True and org_name is not in enable_orgs
        feedback_config = {
            'modules': {'utilizations': {'enable': True, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = None
        assert instance.is_enabled_utilizations_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True and org_name is in enable_orgs
        feedback_config = {
            'modules': {'utilizations': {'enable': True, 'enable_orgs': [org_name]}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = SimpleNamespace(
            **{'name': org_name}
        )
        assert instance.is_enabled_utilizations_org(org_name) is True

    def test_is_enabled_utilizations(self):
        instance = FeedbackPlugin()

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_utilizations() is True

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.utilizations.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_utilizations() is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.utilizations.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_utilizations() is False

        # with feedback_config_file enable is False
        feedback_config = {
            'modules': {'utilizations': {'enable': False, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_utilizations() is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True
        feedback_config = {
            'modules': {'utilizations': {'enable': True, 'enable_orgs': []}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_utilizations() is True

    @patch('ckanext.feedback.plugin.feedback_config')
    def test_is_disabled_repeat_post_on_resource_org(self, mock_feedback_config):
        instance = FeedbackPlugin()
        org_name = 'example_org_name'

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource_org(org_name) is False

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.resources.comment.repeat_post_limit.enable'] = True
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource_org(org_name) is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.resources.comment.repeat_post_limit.enable'] = False
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource_org(org_name) is False

        # with feedback_config_file enable is False and org_name is not in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {
                        'repeat_post_limit': {'enable': False, 'enable_orgs': []}
                    }
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = None
        assert instance.is_disabled_repeat_post_on_resource_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is False and org_name is in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {
                        'repeat_post_limit': {
                            'enable': False,
                            'enable_orgs': [org_name],
                        }
                    }
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = SimpleNamespace(
            **{'name': org_name}
        )
        assert instance.is_disabled_repeat_post_on_resource_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True and org_name is not in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {
                        'repeat_post_limit': {'enable': True, 'enable_orgs': []}
                    }
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = None
        assert instance.is_disabled_repeat_post_on_resource_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True and org_name is in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {
                        'repeat_post_limit': {'enable': True, 'enable_orgs': [org_name]}
                    }
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = SimpleNamespace(
            **{'name': org_name}
        )
        assert instance.is_disabled_repeat_post_on_resource_org(org_name) is True

    def test_is_disabled_repeat_post_on_resource(self):
        instance = FeedbackPlugin()

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource() is False

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.resources.comment.repeat_post_limit.enable'] = True
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource() is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.resources.comment.repeat_post_limit.enable'] = False
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource() is False

        # with feedback_config_file enable is False
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {
                        'repeat_post_limit': {'enable': False, 'enable_orgs': []}
                    }
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource() is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {
                        'repeat_post_limit': {'enable': True, 'enable_orgs': []}
                    }
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource() is True

    @patch('ckanext.feedback.plugin.feedback_config')
    def test_is_enabled_rating_org(self, mock_feedback_config):
        instance = FeedbackPlugin()
        org_name = 'example_org_name'

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_rating_org(org_name) is False

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.resources.comment.rating.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_rating_org(org_name) is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.resources.comment.rating.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_rating_org(org_name) is False

        # with feedback_config_file enable is False and org_name is not in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {'rating': {'enable': False, 'enable_orgs': []}}
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = None
        assert instance.is_enabled_rating_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is False and org_name is in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {'rating': {'enable': False, 'enable_orgs': [org_name]}}
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = SimpleNamespace(
            **{'name': org_name}
        )
        assert instance.is_enabled_rating_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True and org_name is not in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {'rating': {'enable': True, 'enable_orgs': []}}
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = None
        assert instance.is_enabled_rating_org(org_name) is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True and org_name is in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {'rating': {'enable': True, 'enable_orgs': [org_name]}}
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        mock_feedback_config.get_organization.return_value = SimpleNamespace(
            **{'name': org_name}
        )
        assert instance.is_enabled_rating_org(org_name) is True

    def test_is_enabled_rating(self):
        instance = FeedbackPlugin()

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_rating() is False

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.resources.comment.rating.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_rating() is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.resources.comment.rating.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_rating() is False

        # with feedback_config_file enable is False
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {'rating': {'enable': False, 'enable_orgs': []}}
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_rating() is False
        os.remove('/srv/app/feedback_config.json')

        # with feedback_config_file enable is True
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {'rating': {'enable': True, 'enable_orgs': []}}
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_rating() is True

    def test_is_base_public_folder_bs3(self):
        instance = FeedbackPlugin()
        assert instance.is_base_public_folder_bs3() is False

        config['ckan.base_public_folder'] = 'public-bs3'
        instance.update_config(config)
        assert instance.is_base_public_folder_bs3() is True

    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_downloads_org')
    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_utilizations_org')
    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_resources_org')
    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_rating_org')
    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.utilization_summary_service')
    @patch('ckanext.feedback.plugin.resource_summary_service')
    def test_before_dataset_view_with_True(
        self,
        mock_resource_summary_service,
        mock_utilization_summary_service,
        mock_download_summary_service,
        mock_is_enabled_rating_org,
        mock_is_enabled_resources_org,
        mock_is_enabled_utilizations_org,
        mock_is_enabled_downloads_org,
    ):
        instance = FeedbackPlugin()

        mock_is_enabled_rating_org.return_value = False
        mock_is_enabled_resources_org.return_value = True
        mock_is_enabled_utilizations_org.return_value = True
        mock_is_enabled_downloads_org.return_value = True

        mock_resource_summary_service.get_package_comments.return_value = 9999
        mock_resource_summary_service.get_package_rating.return_value = 23.333
        mock_utilization_summary_service.get_package_utilizations.return_value = 9999
        mock_utilization_summary_service.get_package_issue_resolutions.return_value = (
            9999
        )
        mock_download_summary_service.get_package_downloads.return_value = 9999

        dataset = factories.Dataset()

        instance.before_dataset_view(dataset)
        assert dataset['extras'] == [
            {'key': _('Downloads'), 'value': 9999},
            {'key': _('Utilizations'), 'value': 9999},
            {'key': _('Issue Resolutions'), 'value': 9999},
            {'key': _('Comments'), 'value': 9999},
        ]

        mock_is_enabled_rating_org.return_value = True

        dataset['extras'] = []
        instance.before_dataset_view(dataset)
        assert dataset['extras'] == [
            {'key': _('Downloads'), 'value': 9999},
            {'key': _('Utilizations'), 'value': 9999},
            {'key': _('Issue Resolutions'), 'value': 9999},
            {'key': _('Comments'), 'value': 9999},
            {'key': _('Rating'), 'value': 23.3},
        ]

    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_downloads_org')
    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_utilizations_org')
    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_resources_org')
    def test_before_dataset_view_with_False(
        self,
        mock_is_enabled_resources_org,
        mock_is_enabled_utilizations_org,
        mock_is_enabled_downloads_org,
    ):
        instance = FeedbackPlugin()

        mock_is_enabled_resources_org.return_value = False
        mock_is_enabled_utilizations_org.return_value = False
        mock_is_enabled_downloads_org.return_value = False
        dataset = factories.Dataset()
        dataset['extras'] = [
            'test',
        ]
        before_dataset = dataset

        instance.before_dataset_view(dataset)
        assert before_dataset == dataset

    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_downloads_org')
    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_utilizations_org')
    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_resources_org')
    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_rating_org')
    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.utilization_summary_service')
    @patch('ckanext.feedback.plugin.resource_summary_service')
    def test_before_resource_show_with_True(
        self,
        mock_resource_summary_service,
        mock_utilization_summary_service,
        mock_download_summary_service,
        mock_is_enabled_rating_org,
        mock_is_enabled_resources_org,
        mock_is_enabled_utilizations_org,
        mock_is_enabled_downloads_org,
    ):
        instance = FeedbackPlugin()

        mock_is_enabled_rating_org.return_value = False
        mock_is_enabled_resources_org.return_value = True
        mock_is_enabled_utilizations_org.return_value = True
        mock_is_enabled_downloads_org.return_value = True

        mock_resource_summary_service.get_resource_comments.return_value = 9999
        mock_resource_summary_service.get_resource_rating.return_value = 23.333
        mock_utilization_summary_service.get_resource_utilizations.return_value = 9999
        mock_utilization_summary_service.get_resource_issue_resolutions.return_value = (
            9999
        )
        mock_download_summary_service.get_resource_downloads.return_value = 9999

        resource = factories.Resource()

        instance.before_resource_show(resource)
        assert resource[_('Downloads')] == 9999
        assert resource[_('Utilizations')] == 9999
        assert resource[_('Issue Resolutions')] == 9999
        assert resource[_('Comments')] == 9999

        mock_is_enabled_rating_org.return_value = True
        instance.before_resource_show(resource)
        assert resource[_('Rating')] == 23.3

    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_downloads_org')
    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_utilizations_org')
    @patch('ckanext.feedback.plugin.FeedbackPlugin.is_enabled_resources_org')
    def test_before_resource_show_with_False(
        self,
        mock_is_enabled_resources_org,
        mock_is_enabled_utilizations_org,
        mock_is_enabled_downloads_org,
    ):
        instance = FeedbackPlugin()

        mock_is_enabled_resources_org.return_value = False
        mock_is_enabled_utilizations_org.return_value = False
        mock_is_enabled_downloads_org.return_value = False
        resource = factories.Resource()
        resource['extras'] = [
            'test',
        ]
        before_resource = resource

        instance.before_resource_show(resource)
        assert before_resource == resource
