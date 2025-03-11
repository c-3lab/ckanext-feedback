import json
import os
from unittest.mock import patch

import pytest
from ckan import model
from ckan.common import _, config
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_download_monthly_tables,
    create_download_tables,
    create_resource_like_tables,
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
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)
        create_download_monthly_tables(engine)

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

    @patch('ckanext.feedback.plugin.download')
    @patch('ckanext.feedback.plugin.resource')
    @patch('ckanext.feedback.plugin.utilization')
    @patch('ckanext.feedback.plugin.likes')
    @patch('ckanext.feedback.plugin.admin')
    def test_get_blueprint(
        self,
        mock_admin,
        mock_likes,
        mock_utilization,
        mock_resource,
        mock_download,
    ):
        instance = FeedbackPlugin()

        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = True
        mock_admin.get_admin_blueprint.return_value = 'admin_bp'
        mock_likes.get_likes_blueprint.return_value = 'likes_bp'
        mock_download.get_download_blueprint.return_value = 'download_bp'
        mock_resource.get_resource_comment_blueprint.return_value = 'resource_bp'
        mock_utilization.get_utilization_blueprint.return_value = 'utilization_bp'

        expected_blueprints = [
            'download_bp',
            'resource_bp',
            'utilization_bp',
            'likes_bp',
            'admin_bp',
        ]

        actual_blueprints = instance.get_blueprint()

        assert actual_blueprints == expected_blueprints

        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = (
            False
        )
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = False
        expected_blueprints = ['admin_bp']
        actual_blueprints = instance.get_blueprint()

        assert actual_blueprints == expected_blueprints

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
