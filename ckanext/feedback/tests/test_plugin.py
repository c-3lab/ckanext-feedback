import json
import os
from unittest.mock import patch

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
