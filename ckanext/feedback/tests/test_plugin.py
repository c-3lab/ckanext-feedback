import json
import os
from unittest.mock import patch

import pytest
from ckan import model
from ckan.common import config

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
        if os.path.isfile('/etc/ckan/feedback_config.json'):
            os.remove('/etc/ckan/feedback_config.json')

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

        # with .ini file enable is opposite from feedback_config.json
        config['ckan.feedback.utilizations.enable'] = False
        config['ckan.feedback.resources.enable'] = False
        config['ckan.feedback.downloads.enable'] = False
        config['ckan.feedback.resources.comment.repeat_post_limit.enable'] = True
        config['ckan.feedback.resources.comment.rating.enable'] = True
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

    @patch('ckanext.feedback.plugin.toolkit')
    def test_update_config_attribute_error(self, mock_toolkit):
        instance = FeedbackPlugin()
        feedback_config = {'modules': {}}
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

    def test_is_enabled_downloads_org(self):
        instance = FeedbackPlugin()
        org_id = 'example_org_id'

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_downloads_org(org_id) is True

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.downloads.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_downloads_org(org_id) is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.downloads.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_downloads_org(org_id) is False

        # with feedback_config_file enable is False and org_id is not in enable_orgs
        feedback_config = {
            'modules': {'downloads': {'enable': False, 'enable_orgs': []}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_downloads_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is False and org_id is in enable_orgs
        feedback_config = {
            'modules': {'downloads': {'enable': False, 'enable_orgs': [org_id]}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_downloads_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True and org_id is not in enable_orgs
        feedback_config = {
            'modules': {'downloads': {'enable': True, 'enable_orgs': []}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_downloads_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True and org_id is in enable_orgs
        feedback_config = {
            'modules': {'downloads': {'enable': True, 'enable_orgs': [org_id]}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_downloads_org(org_id) is True
        os.remove('/etc/ckan/feedback_config.json')

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
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_downloads() is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True
        feedback_config = {
            'modules': {'downloads': {'enable': True, 'enable_orgs': []}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_downloads() is True

    def test_is_enabled_resources_org(self):
        instance = FeedbackPlugin()
        org_id = 'example_org_id'

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_resources_org(org_id) is True

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.resources.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_resources_org(org_id) is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.resources.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_resources_org(org_id) is False

        # with feedback_config_file enable is False and org_id is not in enable_orgs
        feedback_config = {
            'modules': {'resources': {'enable': False, 'enable_orgs': []}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_resources_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is False and org_id is in enable_orgs
        feedback_config = {
            'modules': {'resources': {'enable': False, 'enable_orgs': [org_id]}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_resources_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True and org_id is not in enable_orgs
        feedback_config = {
            'modules': {'resources': {'enable': True, 'enable_orgs': []}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_resources_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True and org
        feedback_config = {
            'modules': {'resources': {'enable': True, 'enable_orgs': [org_id]}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_resources_org(org_id) is True

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
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_resources() is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True
        feedback_config = {
            'modules': {'resources': {'enable': True, 'enable_orgs': []}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_resources() is True

    def test_is_enabled_utilizations_org(self):
        instance = FeedbackPlugin()
        org_id = 'example_org_id'

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_utilizations_org(org_id) is True

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.utilizations.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_utilizations_org(org_id) is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.utilizations.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_utilizations_org(org_id) is False

        # with feedback_config_file enable is False and org_id is not in enable_orgs
        feedback_config = {
            'modules': {'utilizations': {'enable': False, 'enable_orgs': []}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_utilizations_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is False and org_id is in enable_orgs
        feedback_config = {
            'modules': {'utilizations': {'enable': False, 'enable_orgs': [org_id]}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_utilizations_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True and org_id is not in enable_orgs
        feedback_config = {
            'modules': {'utilizations': {'enable': True, 'enable_orgs': []}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_utilizations_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True and org_id is in enable_orgs
        feedback_config = {
            'modules': {'utilizations': {'enable': True, 'enable_orgs': [org_id]}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_utilizations_org(org_id) is True

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
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_utilizations() is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True
        feedback_config = {
            'modules': {'utilizations': {'enable': True, 'enable_orgs': []}}
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_utilizations() is True

    def test_is_disabled_repeat_post_on_resource_org(self):
        instance = FeedbackPlugin()
        org_id = 'example_org_id'

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource_org(org_id) is False

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.resources.comment.repeat_post_limit.enable'] = True
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource_org(org_id) is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.resources.comment.repeat_post_limit.enable'] = False
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource_org(org_id) is False

        # with feedback_config_file enable is False and org_id is not in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {
                        'repeat_post_limit': {'enable': False, 'enable_orgs': []}
                    }
                }
            }
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is False and org_id is in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {
                        'repeat_post_limit': {'enable': False, 'enable_orgs': [org_id]}
                    }
                }
            }
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True and org_id is not in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {
                        'repeat_post_limit': {'enable': True, 'enable_orgs': []}
                    }
                }
            }
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True and org_id is in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {
                        'repeat_post_limit': {'enable': True, 'enable_orgs': [org_id]}
                    }
                }
            }
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource_org(org_id) is True

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
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource() is False
        os.remove('/etc/ckan/feedback_config.json')

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
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_disabled_repeat_post_on_resource() is True

    def test_is_enabled_rating_org(self):
        instance = FeedbackPlugin()
        org_id = 'example_org_id'

        # without feedback_config_file and .ini file
        instance.update_config(config)
        assert instance.is_enabled_rating_org(org_id) is False

        # without feedback_config_file, .ini file enable is True
        config['ckan.feedback.resources.comment.rating.enable'] = True
        instance.update_config(config)
        assert instance.is_enabled_rating_org(org_id) is True

        # without feedback_config_file, .ini file enable is False
        config['ckan.feedback.resources.comment.rating.enable'] = False
        instance.update_config(config)
        assert instance.is_enabled_rating_org(org_id) is False

        # with feedback_config_file enable is False and org_id is not in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {'rating': {'enable': False, 'enable_orgs': []}}
                }
            }
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_rating_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is False and org_id is in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {'rating': {'enable': False, 'enable_orgs': [org_id]}}
                }
            }
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_rating_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True and org_id is not in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {'rating': {'enable': True, 'enable_orgs': []}}
                }
            }
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_rating_org(org_id) is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True and org_id is in enable_orgs
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {'rating': {'enable': True, 'enable_orgs': [org_id]}}
                }
            }
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_rating_org(org_id) is True

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
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_rating() is False
        os.remove('/etc/ckan/feedback_config.json')

        # with feedback_config_file enable is True
        feedback_config = {
            'modules': {
                'resources': {
                    'comments': {'rating': {'enable': True, 'enable_orgs': []}}
                }
            }
        }
        with open('/etc/ckan/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.update_config(config)
        assert instance.is_enabled_rating() is True
