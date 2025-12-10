import json
import os
from unittest.mock import MagicMock, patch

import pytest
from ckan import model
from ckan.common import _, config
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.plugin import FeedbackPlugin
from ckanext.feedback.services.common.config import FeedbackConfig

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
        try:
            os.remove('/srv/app/feedback_config.json')
        except FileNotFoundError:
            pass
        instance.update_config(config)
        assert FeedbackConfig().is_feedback_config_file is False

        # without .ini file
        feedback_config = {'modules': {}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)

        instance.update_config(config)
        assert FeedbackConfig().is_feedback_config_file is True

    def test_get_commands(self):
        instance = FeedbackPlugin()
        commands = instance.get_commands()
        assert len(commands) == 1
        assert commands[0].name == 'feedback'

    @patch('ckanext.feedback.plugin.plugins.plugin_loaded')
    @patch('ckanext.feedback.plugin.download')
    @patch('ckanext.feedback.plugin.resource')
    @patch('ckanext.feedback.plugin.utilization')
    @patch('ckanext.feedback.plugin.likes')
    @patch('ckanext.feedback.plugin.admin')
    @patch('ckanext.feedback.plugin.api')
    @patch('ckanext.feedback.views.datastore_download.get_datastore_download_blueprint')
    def test_get_blueprint(
        self,
        mock_get_datastore_download_blueprint,
        mock_api,
        mock_admin,
        mock_likes,
        mock_utilization,
        mock_resource,
        mock_download,
        mock_plugin_loaded,
    ):
        instance = FeedbackPlugin()

        # Mock datastore plugin as loaded
        mock_plugin_loaded.return_value = True

        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = True
        mock_api.get_feedback_api_blueprint.return_value = 'api_bp'
        mock_admin.get_admin_blueprint.return_value = 'admin_bp'
        mock_likes.get_likes_blueprint.return_value = 'likes_bp'
        mock_download.get_download_blueprint.return_value = 'download_bp'
        mock_resource.get_resource_comment_blueprint.return_value = 'resource_bp'
        mock_utilization.get_utilization_blueprint.return_value = 'utilization_bp'
        mock_get_datastore_download_blueprint.return_value = 'datastore_download_bp'

        expected_blueprints = [
            'datastore_download_bp',
            'download_bp',
            'resource_bp',
            'utilization_bp',
            'likes_bp',
            'admin_bp',
            'api_bp',
        ]

        actual_blueprints = instance.get_blueprint()

        assert actual_blueprints == expected_blueprints

        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = (
            False
        )
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = False
        expected_blueprints = ['admin_bp', 'api_bp']
        actual_blueprints = instance.get_blueprint()

        assert actual_blueprints == expected_blueprints

    @patch('ckanext.feedback.plugin.plugins.plugin_loaded')
    @patch('ckanext.feedback.plugin.download')
    def test_get_blueprint_datastore_not_loaded(
        self,
        mock_download,
        mock_plugin_loaded,
    ):
        """Test when datastore plugin is not loaded"""
        instance = FeedbackPlugin()

        # Mock datastore plugin as NOT loaded
        mock_plugin_loaded.return_value = False
        mock_download.get_download_blueprint.return_value = 'download_bp'

        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = (
            False
        )
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = False

        blueprints = instance.get_blueprint()

        # Should only have download_bp (no datastore_download_bp)
        assert 'download_bp' in blueprints

    def test_is_base_public_folder_bs3(self):
        instance = FeedbackPlugin()
        assert instance.is_base_public_folder_bs3() is False

        config['ckan.base_public_folder'] = 'public-bs3'
        instance.update_config(config)
        assert instance.is_base_public_folder_bs3() is True

    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.utilization_summary_service')
    @patch('ckanext.feedback.plugin.resource_summary_service')
    @patch('ckanext.feedback.plugin.resource_likes_service')
    def test_before_dataset_view_with_True(
        self,
        mock_resource_likes_service,
        mock_resource_summary_service,
        mock_utilization_summary_service,
        mock_download_summary_service,
    ):
        instance = FeedbackPlugin()

        config[
            f"{FeedbackConfig().resource_comment.rating.get_ckan_conf_str()}.enable"
        ] = False
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = True

        mock_resource_summary_service.get_package_comments.return_value = 9999
        mock_resource_summary_service.get_package_rating.return_value = 23.333
        mock_utilization_summary_service.get_package_utilizations.return_value = 9999
        mock_utilization_summary_service.get_package_issue_resolutions.return_value = (
            9999
        )
        mock_download_summary_service.get_package_downloads.return_value = 9999
        mock_resource_likes_service.get_package_like_count.return_value = 9999

        dataset = factories.Dataset()

        instance.before_dataset_view(dataset)
        assert dataset['extras'] == [
            {'key': _('Downloads'), 'value': 9999},
            {'key': _('Utilizations'), 'value': 9999},
            {'key': _('Issue Resolutions'), 'value': 9999},
            {'key': _('Comments'), 'value': 9999},
            {'key': _('Number of Likes'), 'value': 9999},
        ]

        config[
            f"{FeedbackConfig().resource_comment.rating.get_ckan_conf_str()}.enable"
        ] = True

        dataset['extras'] = []
        instance.before_dataset_view(dataset)
        assert dataset['extras'] == [
            {'key': _('Downloads'), 'value': 9999},
            {'key': _('Utilizations'), 'value': 9999},
            {'key': _('Issue Resolutions'), 'value': 9999},
            {'key': _('Comments'), 'value': 9999},
            {'key': _('Rating'), 'value': 23.3},
            {'key': _('Number of Likes'), 'value': 9999},
        ]

    def test_before_dataset_view_with_False(
        self,
    ):
        instance = FeedbackPlugin()

        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = (
            False
        )
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = False
        dataset = factories.Dataset()
        dataset['extras'] = [
            'test',
        ]
        before_dataset = dataset

        instance.before_dataset_view(dataset)
        assert before_dataset == dataset

    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.utilization_summary_service')
    @patch('ckanext.feedback.plugin.resource_summary_service')
    @patch('ckanext.feedback.plugin.resource_likes_service')
    def test_before_resource_show_with_True(
        self,
        mock_resource_likes_service,
        mock_resource_summary_service,
        mock_utilization_summary_service,
        mock_download_summary_service,
    ):
        instance = FeedbackPlugin()

        config[
            f"{FeedbackConfig().resource_comment.rating.get_ckan_conf_str()}.enable"
        ] = False
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = True

        mock_resource_summary_service.get_resource_comments.return_value = 9999
        mock_resource_summary_service.get_resource_rating.return_value = 23.333
        mock_utilization_summary_service.get_resource_utilizations.return_value = 9999
        mock_utilization_summary_service.get_resource_issue_resolutions.return_value = (
            9999
        )
        mock_download_summary_service.get_resource_downloads.return_value = 9999
        mock_resource_likes_service.get_resource_like_count.return_value = 9999

        resource = factories.Resource()

        instance.before_resource_show(resource)
        assert resource[_('Downloads')] == 9999
        assert resource[_('Utilizations')] == 9999
        assert resource[_('Issue Resolutions')] == 9999
        assert resource[_('Comments')] == 9999
        assert resource[_('Number of Likes')] == 9999

        config[
            f"{FeedbackConfig().resource_comment.rating.get_ckan_conf_str()}.enable"
        ] = True
        instance.before_resource_show(resource)
        assert resource[_('Rating')] == 23.3

    def test_before_resource_show_with_False(
        self,
    ):
        instance = FeedbackPlugin()

        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = (
            False
        )
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = False
        resource = factories.Resource()
        resource['extras'] = [
            'test',
        ]
        before_resource = resource

        instance.before_resource_show(resource)
        assert before_resource == resource

    @patch('ckanext.feedback.plugin.plugins.plugin_loaded')
    def test_before_resource_show_datastore_not_loaded(
        self,
        mock_plugin_loaded,
    ):
        """Test that datastore_active is set to False
        when datastore plugin is not loaded"""
        instance = FeedbackPlugin()

        # Mock datastore plugin as NOT loaded
        mock_plugin_loaded.return_value = False

        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = (
            False
        )
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = False

        resource = factories.Resource()
        resource['datastore_active'] = True  # Initially True

        instance.before_resource_show(resource)

        # Should be set to False
        assert resource['datastore_active'] is False

    @patch('ckanext.feedback.plugin.plugins.plugin_loaded')
    def test_before_resource_show_datastore_loaded(
        self,
        mock_plugin_loaded,
    ):
        """Test that datastore_active is NOT modified when datastore plugin is loaded"""
        instance = FeedbackPlugin()

        # Mock datastore plugin as loaded
        mock_plugin_loaded.return_value = True

        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = (
            False
        )
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = False

        resource = factories.Resource()
        resource['datastore_active'] = True  # Initially True

        instance.before_resource_show(resource)

        # Should remain True (not modified)
        assert resource['datastore_active'] is True

    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.utilization_summary_service')
    @patch('ckanext.feedback.plugin.resource_summary_service')
    @patch('ckanext.feedback.plugin.resource_likes_service')
    @patch('ckanext.feedback.plugin._')
    def test_before_resource_show_with_translation(
        self,
        mock_translation,
        mock_resource_likes_service,
        mock_resource_summary_service,
        mock_utilization_summary_service,
        mock_download_summary_service,
    ):
        instance = FeedbackPlugin()

        config[
            f"{FeedbackConfig().resource_comment.rating.get_ckan_conf_str()}.enable"
        ] = True
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = True

        # Mock translation function to return Japanese
        def mock_translate(key):
            translations = {
                'Downloads': 'ダウンロード数',
                'Utilizations': '活用事例数',
                'Issue Resolutions': '課題解決数',
                'Comments': 'コメント数',
                'Rating': '評価',
                'Number of Likes': 'いいね数',
            }
            return translations.get(key, key)

        mock_translation.side_effect = mock_translate

        mock_resource_summary_service.get_resource_comments.return_value = 5
        mock_resource_summary_service.get_resource_rating.return_value = 4.5
        mock_utilization_summary_service.get_resource_utilizations.return_value = 3
        mock_utilization_summary_service.get_resource_issue_resolutions.return_value = 2
        mock_download_summary_service.get_resource_downloads.return_value = 10
        mock_resource_likes_service.get_resource_like_count.return_value = 8

        resource = factories.Resource()
        # Add English keys that should be removed
        resource['Downloads'] = 0
        resource['Utilizations'] = 0
        resource['Issue Resolutions'] = 0
        resource['Comments'] = 0
        resource['Rating'] = 0
        resource['Number of Likes'] = 0

        instance.before_resource_show(resource)

        # Check that English keys were removed and Japanese keys were added
        assert 'Downloads' not in resource
        assert 'Utilizations' not in resource
        assert 'Issue Resolutions' not in resource
        assert 'Comments' not in resource
        assert 'Rating' not in resource
        assert 'Number of Likes' not in resource

        assert resource['ダウンロード数'] == 10
        assert resource['活用事例数'] == 3
        assert resource['課題解決数'] == 2
        assert resource['コメント数'] == 5
        assert resource['評価'] == 4.5
        assert resource['いいね数'] == 8

    @patch('ckanext.feedback.plugin.FeedbackUpload')
    def test_get_uploader(self, mock_feedback_upload):
        upload_to = 'feedback_storage_path'
        old_filename = 'image.png'

        mock_feedback_upload.return_value = 'feedback_upload'

        instance = FeedbackPlugin()
        instance.get_uploader(upload_to, old_filename)

        mock_feedback_upload.assert_called_once_with(upload_to, old_filename)

    @patch('ckanext.feedback.plugin.FeedbackUpload')
    def test_get_uploader_not_feedback_storage_path(self, mock_feedback_upload):
        upload_to = 'not_feedback_storage_path'
        old_filename = 'image.png'

        instance = FeedbackPlugin()
        instance.get_uploader(upload_to, old_filename)

        mock_feedback_upload.assert_not_called()

    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.utilization_summary_service')
    @patch('ckanext.feedback.plugin.resource_summary_service')
    @patch('ckanext.feedback.plugin.resource_likes_service')
    def test_before_resource_show_with_translation_wrapper(
        self,
        mock_resource_likes_service,
        mock_resource_summary_service,
        mock_utilization_summary_service,
        mock_download_summary_service,
    ):
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = True
        config[
            f"{FeedbackConfig().resource_comment.rating.get_ckan_conf_str()}.enable"
        ] = True
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = True

        mock_resource_summary_service.get_resource_comments.return_value = 9999
        mock_resource_summary_service.get_resource_rating.return_value = 23.333
        mock_utilization_summary_service.get_resource_utilizations.return_value = 9999
        mock_utilization_summary_service.get_resource_issue_resolutions.return_value = (
            9999
        )
        mock_download_summary_service.get_resource_downloads.return_value = 9999
        mock_resource_likes_service.get_resource_like_count.return_value = 9999

        instance = FeedbackPlugin()
        resource = factories.Resource()

        with patch('ckanext.feedback.plugin._', new=lambda s: f'*{s}*'):
            updated = instance.before_resource_show(resource)

        assert updated['*Downloads*'] == 9999
        assert updated['*Utilizations*'] == 9999
        assert updated['*Issue Resolutions*'] == 9999
        assert updated['*Comments*'] == 9999
        assert updated['*Rating*'] == 23.3
        assert updated['*Number of Likes*'] == 9999

    @patch('ckanext.feedback.plugin.config')
    def test_get_solr_url_with_ckan_solr_url(self, mock_config):
        """Test _get_solr_url() with ckan.solr_url config"""
        instance = FeedbackPlugin()
        mock_config.get.side_effect = lambda key: (
            'http://solr-test:8983/solr/ckan' if key == 'ckan.solr_url' else None
        )
        result = instance._get_solr_url()
        assert result == 'http://solr-test:8983/solr/ckan'

    @patch('ckanext.feedback.plugin.config')
    def test_get_solr_url_with_solr_url(self, mock_config):
        """Test _get_solr_url() with solr_url config"""
        instance = FeedbackPlugin()
        mock_config.get.side_effect = lambda key: (
            'http://custom-solr:8983/solr/ckan' if key == 'solr_url' else None
        )
        result = instance._get_solr_url()
        assert result == 'http://custom-solr:8983/solr/ckan'

    @patch('ckanext.feedback.plugin.config')
    def test_get_solr_url_default(self, mock_config):
        """Test _get_solr_url() with default fallback"""
        instance = FeedbackPlugin()
        mock_config.get.return_value = None
        result = instance._get_solr_url()
        assert result == 'http://solr:8983/solr/ckan'

    @patch('ckanext.feedback.plugin.requests')
    def test_field_exists_in_solr_exception(self, mock_requests):
        """Test _field_exists_in_solr() when exception occurs"""
        instance = FeedbackPlugin()
        mock_requests.get.side_effect = Exception('Connection error')
        result = instance._field_exists_in_solr('test_field')
        assert result is False

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    def test_add_solr_field_already_exists(self, mock_requests, mock_log):
        """Test _add_solr_field() when field already exists"""
        instance = FeedbackPlugin()
        existing_fields = ['downloads_total_i', 'likes_total_i']
        instance._add_solr_field(
            'http://solr:8983/solr/ckan/schema', 'downloads_total_i', existing_fields
        )
        mock_log.debug.assert_called_once_with(
            "Field 'downloads_total_i' already exists"
        )
        mock_requests.post.assert_not_called()

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    def test_add_solr_field_error_response(self, mock_requests, mock_log):
        """Test _add_solr_field() when response status is not 200/201"""
        instance = FeedbackPlugin()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_requests.post.return_value = mock_response
        instance._add_solr_field('http://solr:8983/solr/ckan/schema', 'test_field', [])
        mock_log.error.assert_called_once()
        assert 'Failed to add' in str(mock_log.error.call_args)

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    def test_add_solr_field_request_exception(self, mock_requests, mock_log):
        """Test _add_solr_field() when RequestException occurs"""
        instance = FeedbackPlugin()
        # Set requests.exceptions to the real module so exceptions can be caught
        import requests.exceptions

        mock_requests.exceptions = requests.exceptions
        # Create a real RequestException instance
        from requests.exceptions import RequestException

        mock_requests.post.side_effect = RequestException('Timeout')
        instance._add_solr_field('http://solr:8983/solr/ckan/schema', 'test_field', [])
        mock_log.error.assert_called_once()
        assert 'Error adding' in str(mock_log.error.call_args)

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    def test_setup_solr_schema_api_not_200(self, mock_requests, mock_log):
        """Test _setup_solr_schema() when Schema API returns non-200 status"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests.get.return_value = mock_response

        instance._setup_solr_schema()
        mock_log.warning.assert_called_once()
        assert 'Schema API returned status' in str(mock_log.warning.call_args)

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    def test_setup_solr_schema_api_exception(self, mock_requests, mock_log):
        """Test _setup_solr_schema() when Schema API request fails"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        # Set requests.exceptions to the real module so exceptions can be caught
        import requests.exceptions

        mock_requests.exceptions = requests.exceptions
        # Create a real RequestException instance
        from requests.exceptions import RequestException

        mock_requests.get.side_effect = RequestException('Connection error')

        instance._setup_solr_schema()
        # Check that warning was called (could be called multiple times)
        assert mock_log.warning.called
        # Check that one of the warning calls contains the expected message
        warning_calls = [str(call) for call in mock_log.warning.call_args_list]
        assert any('Schema API not available' in call for call in warning_calls)

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    def test_setup_solr_schema_unexpected_exception(self, mock_requests, mock_log):
        """Test _setup_solr_schema() when unexpected exception occurs"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        mock_requests.get.side_effect = ValueError('Unexpected error')

        instance._setup_solr_schema()
        mock_log.error.assert_called_once()
        assert 'Unexpected error in Solr schema setup' in str(mock_log.error.call_args)

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.resource_likes_service')
    def test_before_dataset_index_no_package_id(
        self, mock_likes_service, mock_download_service, mock_log
    ):
        """Test before_dataset_index() when package_id is missing"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        pkg_dict = {}
        result = instance.before_dataset_index(pkg_dict)
        assert result == pkg_dict
        mock_download_service.get_package_downloads.assert_not_called()
        mock_likes_service.get_package_like_count.assert_not_called()

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.resource_likes_service')
    def test_before_dataset_index_field_not_exists(
        self, mock_likes_service, mock_download_service, mock_requests, mock_log
    ):
        """Test before_dataset_index() when Solr fields don't exist"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        # Mock field_exists_in_solr to return False
        mock_field_response = MagicMock()
        mock_field_response.status_code = 404
        mock_requests.get.return_value = mock_field_response

        pkg_dict = {'id': 'test-package-id', 'owner_org': 'test-org'}
        result = instance.before_dataset_index(pkg_dict)

        assert 'downloads_total_i' not in result
        assert 'likes_total_i' not in result

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    def test_setup_solr_schema_with_download_and_likes(self, mock_requests, mock_log):
        """Test _setup_solr_schema() when downloads and likes are enabled"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        # Mock successful Schema API response
        mock_fields_response = MagicMock()
        mock_fields_response.status_code = 200
        mock_fields_response.json.return_value = {'fields': []}
        mock_requests.get.return_value = mock_fields_response

        # Mock successful field addition
        mock_add_response = MagicMock()
        mock_add_response.status_code = 200
        mock_requests.post.return_value = mock_add_response

        instance._setup_solr_schema()

        # Verify that both fields were attempted to be added
        assert mock_requests.post.call_count == 2
        mock_log.info.assert_any_call("Solr schema setup completed")

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.resource_likes_service')
    @patch('ckanext.feedback.plugin.config')
    def test_before_dataset_index_fields_exist(
        self,
        mock_config,
        mock_likes_service,
        mock_download_service,
        mock_requests,
        mock_log,
    ):
        """Test before_dataset_index() when Solr fields exist"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        # Mock config.get to return solr_url and enable values
        def config_get_side_effect(key, default=None):
            if key == 'ckan.solr_url' or key == 'solr_url':
                return 'http://solr:8983/solr/ckan'
            # Return True for enable configs
            if 'enable' in key:
                return True
            return default

        mock_config.get.side_effect = config_get_side_effect

        # Mock field_exists_in_solr to return True
        # _field_exists_in_solr calls requests.get with URL like:
        # http://solr:8983/solr/ckan/schema/fields/downloads_total_i
        def requests_get_side_effect(url, **kwargs):
            mock_response = MagicMock()
            if '/fields/downloads_total_i' in url or '/fields/likes_total_i' in url:
                mock_response.status_code = 200
            else:
                mock_response.status_code = 404
            return mock_response

        mock_requests.get.side_effect = requests_get_side_effect

        mock_download_service.get_package_downloads.return_value = 100
        mock_likes_service.get_package_like_count.return_value = 50

        # Use None for owner_org to avoid organization lookup issues
        # When org_id is empty, is_enable returns the enable value directly
        pkg_dict = {'id': 'test-package-id', 'owner_org': None}
        result = instance.before_dataset_index(pkg_dict)

        assert result['downloads_total_i'] == 100
        assert result['likes_total_i'] == 50

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.resource_likes_service')
    def test_before_dataset_index_custom_sort_disabled(
        self, mock_likes_service, mock_download_service, mock_requests, mock_log
    ):
        """Test before_dataset_index() when custom_sort is disabled"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': False},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        pkg_dict = {'id': 'test-package-id', 'owner_org': 'test-org'}
        result = instance.before_dataset_index(pkg_dict)

        assert 'downloads_total_i' not in result
        assert 'likes_total_i' not in result
        mock_download_service.get_package_downloads.assert_not_called()
        mock_likes_service.get_package_like_count.assert_not_called()

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.resource_likes_service')
    def test_before_dataset_index_no_owner_org(
        self, mock_likes_service, mock_download_service, mock_requests, mock_log
    ):
        """Test before_dataset_index() when owner_org is None"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        # Mock field_exists_in_solr to return True
        mock_field_response = MagicMock()
        mock_field_response.status_code = 200
        mock_requests.get.return_value = mock_field_response

        mock_download_service.get_package_downloads.return_value = 100
        mock_likes_service.get_package_like_count.return_value = 50

        pkg_dict = {'id': 'test-package-id'}
        result = instance.before_dataset_index(pkg_dict)

        assert result['downloads_total_i'] == 100
        assert result['likes_total_i'] == 50

    @patch('ckanext.feedback.plugin.log')
    def test_before_dataset_view_package_not_found(self, mock_log):
        """Test before_dataset_view() when package is not found"""
        instance = FeedbackPlugin()
        pkg_dict = {'id': 'non-existent-package'}
        result = instance.before_dataset_view(pkg_dict)
        assert result == pkg_dict
        mock_log.warning.assert_called_once()
        assert 'not found in before_dataset_view' in str(mock_log.warning.call_args)

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    def test_setup_solr_schema_custom_sort_disabled_direct(
        self, mock_requests, mock_log
    ):
        """Test _setup_solr_schema() when custom_sort is disabled (direct test)"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': False},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        instance._setup_solr_schema()

        # Should return early without making any requests
        mock_requests.get.assert_not_called()
        mock_log.debug.assert_called_once_with(
            "Custom sort feature is disabled in feedback_config.json"
        )

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    @patch('ckanext.feedback.services.common.config.config')
    def test_setup_solr_schema_download_disabled(
        self, mock_config, mock_requests, mock_log
    ):
        """Test _setup_solr_schema() when download is disabled"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': False},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        # Mock config.get to return appropriate values
        def config_get_side_effect(key, default=None):
            if key == f"{FeedbackConfig().custom_sort.get_ckan_conf_str()}.enable":
                return True
            elif key == f"{FeedbackConfig().download.get_ckan_conf_str()}.enable":
                return False
            elif key == f"{FeedbackConfig().like.get_ckan_conf_str()}.enable":
                return True
            elif key in ('ckan.solr_url', 'solr_url'):
                return None
            return default

        mock_config.get.side_effect = config_get_side_effect

        # Mock successful Schema API response
        mock_fields_response = MagicMock()
        mock_fields_response.status_code = 200
        mock_fields_response.json.return_value = {'fields': []}
        mock_requests.get.return_value = mock_fields_response

        # Mock successful field addition
        mock_add_response = MagicMock()
        mock_add_response.status_code = 200
        mock_requests.post.return_value = mock_add_response

        instance._setup_solr_schema()

        # Should only add likes_total_i field, not downloads_total_i
        assert mock_requests.post.call_count == 1
        # Verify that the call was for likes_total_i
        call_args = mock_requests.post.call_args
        assert 'likes_total_i' in str(call_args)

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    @patch('ckanext.feedback.services.common.config.config')
    def test_setup_solr_schema_like_disabled(
        self, mock_config, mock_requests, mock_log
    ):
        """Test _setup_solr_schema() when like is disabled"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': True},
                'like': {'enable': False},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        # Mock config.get to return appropriate values
        def config_get_side_effect(key, default=None):
            if key == f"{FeedbackConfig().custom_sort.get_ckan_conf_str()}.enable":
                return True
            elif key == f"{FeedbackConfig().download.get_ckan_conf_str()}.enable":
                return True
            elif key == f"{FeedbackConfig().like.get_ckan_conf_str()}.enable":
                return False
            elif key in ('ckan.solr_url', 'solr_url'):
                return None
            return default

        mock_config.get.side_effect = config_get_side_effect

        # Mock successful Schema API response
        mock_fields_response = MagicMock()
        mock_fields_response.status_code = 200
        mock_fields_response.json.return_value = {'fields': []}
        mock_requests.get.return_value = mock_fields_response

        # Mock successful field addition
        mock_add_response = MagicMock()
        mock_add_response.status_code = 200
        mock_requests.post.return_value = mock_add_response

        instance._setup_solr_schema()

        # Should only add downloads_total_i field, not likes_total_i
        assert mock_requests.post.call_count == 1
        # Verify that the call was for downloads_total_i
        call_args = mock_requests.post.call_args
        assert 'downloads_total_i' in str(call_args)

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.resource_likes_service')
    def test_before_dataset_index_downloads_field_not_exists(
        self, mock_likes_service, mock_download_service, mock_requests, mock_log
    ):
        """Test before_dataset_index() when downloads field doesn't exist
        but download is enabled"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        # Mock field_exists_in_solr: downloads_total_i returns False,
        # likes_total_i returns True
        def requests_get_side_effect(url, **kwargs):
            mock_response = MagicMock()
            if '/fields/downloads_total_i' in url:
                mock_response.status_code = 404  # Field doesn't exist
            elif '/fields/likes_total_i' in url:
                mock_response.status_code = 200  # Field exists
            else:
                mock_response.status_code = 404
            return mock_response

        mock_requests.get.side_effect = requests_get_side_effect

        mock_download_service.get_package_downloads.return_value = 100
        mock_likes_service.get_package_like_count.return_value = 50

        pkg_dict = {'id': 'test-package-id', 'owner_org': None}
        result = instance.before_dataset_index(pkg_dict)

        # downloads_total_i should not be added (field doesn't exist)
        assert 'downloads_total_i' not in result
        # likes_total_i should be added (field exists)
        assert result['likes_total_i'] == 50
        # download service should not be called since field doesn't exist
        mock_download_service.get_package_downloads.assert_not_called()

    @patch('ckanext.feedback.plugin.log')
    @patch('ckanext.feedback.plugin.requests')
    @patch('ckanext.feedback.plugin.download_summary_service')
    @patch('ckanext.feedback.plugin.resource_likes_service')
    def test_before_dataset_index_likes_field_not_exists(
        self, mock_likes_service, mock_download_service, mock_requests, mock_log
    ):
        """Test before_dataset_index() when likes field doesn't exist
        but like is enabled"""
        instance = FeedbackPlugin()
        instance.fb_config = FeedbackConfig()
        feedback_config = {
            'modules': {
                'custom_sort': {'enable': True},
                'download': {'enable': True},
                'like': {'enable': True},
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f, indent=2)
        instance.fb_config.load_feedback_config()

        # Mock field_exists_in_solr: downloads_total_i returns True,
        # likes_total_i returns False
        def requests_get_side_effect(url, **kwargs):
            mock_response = MagicMock()
            if '/fields/downloads_total_i' in url:
                mock_response.status_code = 200  # Field exists
            elif '/fields/likes_total_i' in url:
                mock_response.status_code = 404  # Field doesn't exist
            else:
                mock_response.status_code = 404
            return mock_response

        mock_requests.get.side_effect = requests_get_side_effect

        mock_download_service.get_package_downloads.return_value = 100
        mock_likes_service.get_package_like_count.return_value = 50

        pkg_dict = {'id': 'test-package-id', 'owner_org': None}
        result = instance.before_dataset_index(pkg_dict)

        # downloads_total_i should be added (field exists)
        assert result['downloads_total_i'] == 100
        # likes_total_i should not be added (field doesn't exist)
        assert 'likes_total_i' not in result
        # likes service should not be called since field doesn't exist
        mock_likes_service.get_package_like_count.assert_not_called()
