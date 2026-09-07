from unittest.mock import patch

import pytest
from ckan.common import config

from ckanext.feedback.lib import helpers as feedback_helpers
from ckanext.feedback.services.common.config import FeedbackConfig


@pytest.mark.usefixtures('with_request_context')
class TestHelpers:
    def test_strip_resource_feedback_fields(self):
        resource_dict = {
            'feedback_like_count': 1,
            'いいね数': 2,
            'name': 'example.csv',
        }

        feedback_helpers.strip_resource_feedback_fields(resource_dict)

        assert resource_dict == {'name': 'example.csv'}

    def test_populate_resource_feedback_fields_returns_early_without_ids(self):
        resource_dict = {'id': 'resource-id'}
        assert feedback_helpers.populate_resource_feedback_fields(resource_dict) is resource_dict

        resource_dict = {'package_id': 'package-id'}
        assert feedback_helpers.populate_resource_feedback_fields(resource_dict) is resource_dict

    @patch('ckanext.feedback.lib.helpers.model.Package.get')
    def test_populate_resource_feedback_fields_returns_early_when_package_missing(
        self,
        mock_package_get,
    ):
        mock_package_get.return_value = None
        resource_dict = {'id': 'resource-id', 'package_id': 'missing-package-id'}

        assert feedback_helpers.populate_resource_feedback_fields(resource_dict) is resource_dict

    @patch('ckanext.feedback.lib.helpers.resource_summary_service')
    @patch('ckanext.feedback.lib.helpers.model.Package.get')
    def test_populate_resource_feedback_fields_adds_all_stats(
        self,
        mock_package_get,
        mock_resource_summary_service,
    ):
        mock_package_get.return_value = type('Package', (), {'owner_org': 'test-org-id'})()
        mock_resource_summary_service.get_resource_feedback_stats.return_value = {
            'like_count': 8,
            'downloads': 10,
            'utilizations': 3,
            'comments': 5,
            'rating': 4.5,
            'issue_resolutions': 2,
        }
        config[
            f"{FeedbackConfig().resource_comment.rating.get_ckan_conf_str()}.enable"
        ] = True
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = True

        resource_dict = {'id': 'resource-id', 'package_id': 'package-id'}
        populated = feedback_helpers.populate_resource_feedback_fields(resource_dict)

        assert populated['feedback_downloads'] == 10
        assert populated['feedback_utilizations'] == 3
        assert populated['feedback_issue_resolutions'] == 2
        assert populated['feedback_comments'] == 5
        assert populated['feedback_rating'] == 4.5
        assert populated['feedback_like_count'] == 8

    def test_strip_package_feedback_extras(self):
        package_dict = {
            'extras': [
                {'key': 'feedback_total_like_count', 'value': 1},
                {'key': 'other_key', 'value': 'keep'},
            ]
        }

        feedback_helpers.strip_package_feedback_extras(package_dict)

        assert package_dict['extras'] == [{'key': 'other_key', 'value': 'keep'}]

    @patch('ckanext.feedback.lib.helpers.model.Package.get')
    def test_populate_package_feedback_extras_returns_early_when_package_missing(
        self,
        mock_package_get,
    ):
        mock_package_get.return_value = None
        package_dict = {'id': 'missing-package-id', 'extras': []}

        assert (
            feedback_helpers.populate_package_feedback_extras(package_dict, {})
            is package_dict
        )

    @patch('ckanext.feedback.lib.helpers.model.Package.get')
    def test_populate_package_feedback_extras_updates_existing_extra(
        self,
        mock_package_get,
    ):
        mock_package_get.return_value = type('Package', (), {'owner_org': 'test-org-id'})()
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = False
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = False

        package_dict = {
            'id': 'test-package-id',
            'extras': [{'key': 'feedback_total_like_count', 'value': 0}],
        }

        feedback_helpers.populate_package_feedback_extras(
            package_dict,
            {'like_count': 42},
        )

        assert package_dict['extras'] == [
            {'key': 'feedback_total_like_count', 'value': 42},
        ]

    @patch('ckanext.feedback.lib.helpers.model.Package.get')
    def test_populate_package_feedback_extras_adds_all_stats(
        self,
        mock_package_get,
    ):
        mock_package_get.return_value = type('Package', (), {'owner_org': 'test-org-id'})()
        config[
            f"{FeedbackConfig().resource_comment.rating.get_ckan_conf_str()}.enable"
        ] = True
        config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = True
        config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = True

        package_dict = {'id': 'test-package-id', 'extras': []}
        stats = {
            'like_count': 8,
            'downloads': 10,
            'utilizations': 3,
            'comments': 5,
            'rating': 0,
            'issue_resolutions': 2,
        }

        feedback_helpers.populate_package_feedback_extras(package_dict, stats)

        extras = {extra['key']: extra['value'] for extra in package_dict['extras']}
        assert extras == {
            'feedback_total_downloads': 10,
            'feedback_total_utilizations': 3,
            'feedback_total_issue_resolutions': 2,
            'feedback_total_comments': 5,
            'feedback_average_rating': 0,
            'feedback_total_like_count': 8,
        }

    @pytest.mark.parametrize(
        'field_key,expected',
        [
            ('feedback_like_count', True),
            ('feedback_custom_field', True),
            ('いいね数', True),
            ('name', False),
        ],
    )
    def test_should_hide_resource_field(self, field_key, expected):
        assert feedback_helpers.should_hide_resource_field(field_key) is expected

    @patch(
        'ckanext.feedback.lib.helpers._EXTRAS_KEY_LABEL_GETTERS',
        {
            'feedback_total_like_count': lambda: 'Translated Total Likes',
        },
    )
    def test_get_feedback_field_label_uses_extras_catalog_when_translated(self):
        assert (
            feedback_helpers.get_feedback_field_label('feedback_total_like_count')
            == 'Translated Total Likes'
        )

    @patch('ckanext.feedback.lib.helpers.populate_resource_feedback_fields')
    def test_get_feedback_fields_skips_unpopulated_keys(
        self,
        mock_populate_resource_feedback_fields,
    ):
        mock_populate_resource_feedback_fields.return_value = {
            'feedback_like_count': 1,
        }

        fields = feedback_helpers.get_feedback_fields(
            {'id': 'resource-id', 'package_id': 'package-id'}
        )

        assert len(fields) == 1

    def test_format_resource_items_translates_feedback_keys(self):
        def next_helper(items):
            return items

        items = [
            ('feedback_like_count', 5),
            ('name', 'example.csv'),
        ]

        result = feedback_helpers.format_resource_items(next_helper, items)

        assert result[0][0] == feedback_helpers.get_feedback_field_label(
            'feedback_like_count'
        )
        assert result[0][1] == 5
        assert result[1] == ('name', 'example.csv')
