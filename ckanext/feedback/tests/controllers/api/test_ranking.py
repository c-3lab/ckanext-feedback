from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from ckan.plugins.toolkit import ValidationError

from ckanext.feedback.controllers.api import ranking as DatasetRankingController
from ckanext.feedback.models.download import DownloadMonthly, DownloadSummary
from ckanext.feedback.models.likes import ResourceLike, ResourceLikeMonthly
from ckanext.feedback.models.resource_comment import ResourceCommentSummary
from ckanext.feedback.models.utilization import Utilization


class TestRankingApi:
    @patch('ckanext.feedback.controllers.api.ranking._ranking_controller')
    def test_datasets_ranking(
        self,
        mock_ranking_controller,
    ):
        mock_ranking_controller.get_datasets_ranking.return_value = [
            {
                'rank': 1,
                'group_name': 'group_name1',
                'group_title': 'group_title1',
                'dataset_title': 'dataset_title1',
                'dataset_notes': 'dataset_notes1',
                'dataset_link': 'https://site-url/dataset/dataset_name1',
                'download_count_by_period': 100,
                'total_download_count': 100,
            },
        ]

        context = {}
        data_dict = {
            'top_ranked_limit': '5',
            'period_months_ago': 'all',
            'start_year_month': None,
            'end_year_month': None,
            'aggregation_metric': 'download',
            'organization_name': None,
        }

        result = DatasetRankingController.datasets_ranking(context, data_dict)

        assert result == [
            {
                'rank': 1,
                'group_name': 'group_name1',
                'group_title': 'group_title1',
                'dataset_title': 'dataset_title1',
                'dataset_notes': 'dataset_notes1',
                'dataset_link': 'https://site-url/dataset/dataset_name1',
                'download_count_by_period': 100,
                'total_download_count': 100,
            },
        ]
        mock_ranking_controller.get_datasets_ranking.assert_called_once_with(data_dict)


class TestRankingValidator:
    def test_validate_input_parameters(self):
        controller = DatasetRankingController._ranking_controller
        data_dict = {'top_ranked_limit': '5'}

        controller.validator.validate_input_parameters(data_dict)

    def test_validate_input_parameters_with_invalid_parameter(self):
        controller = DatasetRankingController._ranking_controller
        data_dict = {'test_parameter': '10'}

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_input_parameters(data_dict)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "The following fields are not valid: ['test_parameter']. "
            "Please review the provided input and ensure only these fields "
            "are included: ['top_ranked_limit', 'period_months_ago', "
            "'start_year_month', 'end_year_month', "
            "'aggregation_metric', 'organization_name']."
        )

    def test_validate_top_ranked_limit(self):
        controller = DatasetRankingController._ranking_controller
        top_ranked_limit = '5'

        controller.validator.validate_top_ranked_limit(top_ranked_limit)

    def test_validate_top_ranked_limit_with_invalid_type(self):
        controller = DatasetRankingController._ranking_controller
        top_ranked_limit = 'test'

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_top_ranked_limit(top_ranked_limit)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "The 'top_ranked_limit' must be a number."

    def test_validate_top_ranked_limit_with_invalid_value_under_min(self):
        controller = DatasetRankingController._ranking_controller
        top_ranked_limit = '0'

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_top_ranked_limit(top_ranked_limit)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "The 'top_ranked_limit' must be between 1 and 100."

    def test_validate_top_ranked_limit_with_invalid_value_over_max(self):
        controller = DatasetRankingController._ranking_controller
        top_ranked_limit = '101'

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_top_ranked_limit(top_ranked_limit)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "The 'top_ranked_limit' must be between 1 and 100."

    def test_validate_date_format(self):
        controller = DatasetRankingController._ranking_controller
        date_str = '2024-01'
        field_name = 'start_year_month'

        controller.validator.validate_date_format(date_str, field_name)

    def test_validate_date_format_with_invalid_format(self):
        controller = DatasetRankingController._ranking_controller
        date_str = '2024-1'
        field_name = 'start_year_month'

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_date_format(date_str, field_name)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == "Invalid format for 'start_year_month'. Expected format is YYYY-MM."
        )

    def test_validate_start_year_month_not_before_default(self):
        controller = DatasetRankingController._ranking_controller
        start_year_month = '2024-01'

        controller.validator.validate_start_year_month_not_before_default(
            start_year_month
        )

    def test_validate_start_year_month_not_before_default_with_invalid_value(self):
        controller = DatasetRankingController._ranking_controller
        start_year_month = '2023-03'

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_start_year_month_not_before_default(
                start_year_month
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "The start date must be later than 2023-04."

    def test_validate_end_year_month_not_in_future(self):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        end_year_month = '2023-12'

        controller.validator.validate_end_year_month_not_in_future(
            today, end_year_month
        )

    def test_validate_end_year_month_not_in_future_with_invalid_value(self):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        end_year_month = '2024-02'

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_end_year_month_not_in_future(
                today, end_year_month
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "The selected period cannot be in the future."

    def test_validate_period_months_ago(self):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = '3'

        controller.validator.validate_period_months_ago(today, period_months_ago)

    def test_validate_period_months_ago_with_invalid_type(self):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = 'test'

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_period_months_ago(today, period_months_ago)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "The period must be specified as a numerical value or all."
        )

    def test_validate_period_months_ago_with_invalid_value_under_min(self):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = '0'

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_period_months_ago(today, period_months_ago)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == "The period must be a positive integer (natural number) of 1 or greater."
        )

    def test_validate_period_months_ago_with_invalid_value_over_max(self):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = '13'

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_period_months_ago(today, period_months_ago)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "The selected period is beyond the allowable range. "
            "Only periods up to 2023-04 are allowed."
        )

    def test_validate_aggregation_metric(self):
        controller = DatasetRankingController._ranking_controller
        for aggregation_metric in [
            'download',
            'likes',
            'resource_comments',
            'utilization_comments',
        ]:
            controller.validator.validate_aggregation_metric(aggregation_metric)

    def test_validate_aggregation_metric_with_invalid_value(self):
        controller = DatasetRankingController._ranking_controller
        aggregation_metric = 'test'

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_aggregation_metric(aggregation_metric)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "This is a non-existent aggregation metric."

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    def test_validate_download_function(self, mock_feedback_config):
        controller = DatasetRankingController._ranking_controller

        mock_download = MagicMock()
        mock_download.is_enable.return_value = True
        mock_feedback_config.return_value.download = mock_download

        controller.validator.validate_download_function()

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    def test_validate_download_function_with_disabled_download(
        self, mock_feedback_config
    ):
        controller = DatasetRankingController._ranking_controller

        mock_download = MagicMock()
        mock_download.is_enable.return_value = False
        mock_feedback_config.return_value.download = mock_download

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_download_function()

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "Download function is off. "
            "Please contact the site administrator for assistance."
        )

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    def test_validate_likes_function(self, mock_feedback_config):
        controller = DatasetRankingController._ranking_controller

        mock_likes = MagicMock()
        mock_likes.is_enable.return_value = True
        mock_feedback_config.return_value.like = mock_likes

        controller.validator.validate_likes_function()

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    def test_validate_likes_function_with_disabled_likes(self, mock_feedback_config):
        controller = DatasetRankingController._ranking_controller

        mock_likes = MagicMock()
        mock_likes.is_enable.return_value = False
        mock_feedback_config.return_value.like = mock_likes

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_likes_function()

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "Likes function is off."
            "Please contact the site administrator for assintance."
        )

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    def test_validate_resource_comments_function(self, mock_feedback_config):
        controller = DatasetRankingController._ranking_controller

        mock_resource_comments = MagicMock()
        mock_resource_comments.is_enable.return_value = True
        mock_feedback_config.return_value.resource_comment = mock_resource_comments

        controller.validator.validate_resource_comments_function()

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    def test_validate_resource_comments_function_with_disabled_resource_comments(
        self, mock_feedback_config
    ):
        controller = DatasetRankingController._ranking_controller

        mock_resource_comments = MagicMock()
        mock_resource_comments.is_enable.return_value = False
        mock_feedback_config.return_value.resource_comment = mock_resource_comments

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_resource_comments_function()

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "ResourceComments function is off."
            "Please contact the site administrator for assintance."
        )

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    def test_validate_utilization_comments_function(self, mock_feedback_config):
        controller = DatasetRankingController._ranking_controller

        mock_utilization_comments = MagicMock()
        mock_utilization_comments.is_enable.return_value = True
        mock_feedback_config.return_value.utilization_comment = (
            mock_utilization_comments
        )

        controller.validator.validate_utilization_comments_function()

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    def test_validate_utilization_comments_function_with_disabled_utilization_comments(
        self, mock_feedback_config
    ):
        controller = DatasetRankingController._ranking_controller

        mock_utilization_comments = MagicMock()
        mock_utilization_comments.is_enable.return_value = False
        mock_feedback_config.return_value.utilization_comment = (
            mock_utilization_comments
        )

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_utilization_comments_function()

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "UtilizationComments function is off."
            "Please contact the site administrator for assintance."
        )

    def test_validate_organization_likes_enabled(self):
        controller = DatasetRankingController._ranking_controller
        organization_name = 'test_org1'
        enable_org = ['test_org1']

        controller.validator.validate_organization_likes_enabled(
            organization_name, enable_org
        )

    def test_validate_organization_likes_enabled_with_disabled_organization(self):
        controller = DatasetRankingController._ranking_controller
        organization_name = 'test_org2'
        enable_org = ['test_org1']

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_organization_likes_enabled(
                organization_name, enable_org
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == "An organization with the likes feature disabled has been selected. "
            "Please contact the site administrator for assistance."
        )

    def test_validate_organization_resource_comments_enabled(self):
        controller = DatasetRankingController._ranking_controller
        organization_name = 'test_org1'
        enable_org = ['test_org1']

        controller.validator.validate_organization_resource_comments_enabled(
            organization_name, enable_org
        )

    def test_validate_organization_resource_comments_enabled_with_disabled_organization(
        self,
    ):
        controller = DatasetRankingController._ranking_controller
        organization_name = 'test_org2'
        enable_org = ['test_org1']

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_organization_resource_comments_enabled(
                organization_name, enable_org
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "An organization with the resourceComment "
            "feature disabled has been selected. "
            "Please contact the site administrator for assistance."
        )

    def test_validate_organization_utilization_comments_enabled(self):
        controller = DatasetRankingController._ranking_controller
        organization_name = 'test_org1'
        enable_org = ['test_org1']

        controller.validator.validate_organization_utilization_comments_enabled(
            organization_name, enable_org
        )

    def test_validate_organization_utilization_comments_enabled_with_disabled_organization(  # noqa: E501
        self,
    ):
        controller = DatasetRankingController._ranking_controller
        organization_name = 'test_org2'
        enable_org = ['test_org1']

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_organization_utilization_comments_enabled(
                organization_name, enable_org
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == "An organization with the utilizationComment feature disabled "
            "has been selected. "
            "Please contact the site administrator for assistance."
        )

    @patch('ckanext.feedback.controllers.api.ranking.organization_service')
    def test_validate_organization_name_in_group(self, mock_organization_service):
        controller = DatasetRankingController._ranking_controller
        organization_name = 'test_org1'

        mock_organization_service.get_organization_name_by_name.return_value = (
            organization_name
        )

        controller.validator.validate_organization_name_in_group(organization_name)

    @patch('ckanext.feedback.controllers.api.ranking.organization_service')
    def test_validate_organization_name_in_group_with_invalid_name(
        self, mock_organization_service
    ):
        controller = DatasetRankingController._ranking_controller
        organization_name = 'test_org2'

        mock_organization_service.get_organization_name_by_name.return_value = None

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_organization_name_in_group(organization_name)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "The specified organization does not exist or "
            "may have been deleted. Please enter a valid organization name."
        )

    def test_validate_organization_download_enabled(self):
        controller = DatasetRankingController._ranking_controller
        organization_name = 'test_org1'
        enable_org = ['test_org1']

        controller.validator.validate_organization_download_enabled(
            organization_name, enable_org
        )

    def test_validate_organization_download_enabled_with_disabled_organization(self):
        controller = DatasetRankingController._ranking_controller
        organization_name = 'test_org2'
        enable_org = ['test_org1']

        with pytest.raises(ValidationError) as exc_info:
            controller.validator.validate_organization_download_enabled(
                organization_name, enable_org
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == "An organization with the download feature disabled has been selected. "
            "Please contact the site administrator for assistance."
        )


class TestDateRangeCalculator:
    def test_validate_and_adjust_date_range_full_input(self):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        start_year_month = '2023-07'
        end_year_month = '2023-10'

        with patch.object(
            controller.validator, 'validate_date_format'
        ) as mock_validate_date, patch.object(
            controller.validator, 'validate_start_year_month_not_before_default'
        ) as mock_validate_start, patch.object(
            controller.validator, 'validate_end_year_month_not_in_future'
        ) as mock_validate_end:

            mock_validate_date.return_value = None
            mock_validate_start.return_value = None
            mock_validate_end.return_value = None

            result = controller.date_calculator._validate_and_adjust_date_range(
                today, start_year_month, end_year_month
            )

            assert result == (start_year_month, end_year_month)

    def test_validate_and_adjust_date_range_default_start_date_and_end_date(self):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        start_year_month = None
        end_year_month = None

        result = controller.date_calculator._validate_and_adjust_date_range(
            today, start_year_month, end_year_month
        )

        assert result == ('2023-04', '2023-12')

    def test_calculate_date_range_from_period_correct_range(self):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = '3'

        with patch.object(
            controller.validator, 'validate_period_months_ago'
        ) as mock_validate_period:
            mock_validate_period.return_value = None

            result = controller.date_calculator._calculate_date_range_from_period(
                today, period_months_ago
            )

            assert result == ('2023-10', '2023-12')

    def test_calculate_date_range_from_period_all(self):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = 'all'

        result = controller.date_calculator._calculate_date_range_from_period(
            today, period_months_ago
        )

        assert result == ('2023-04', '2023-12')

    @patch.object(
        DatasetRankingController._ranking_controller.date_calculator,
        '_calculate_date_range_from_period',
    )
    def test_get_year_months_with_period_months_ago(self, mock_calc):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = '3'
        start_year_month = None
        end_year_month = None

        mock_calc.return_value = ('2023-10', '2023-12')

        result = controller.date_calculator.get_year_months(
            today, period_months_ago, start_year_month, end_year_month
        )

        assert result == ('2023-10', '2023-12')
        mock_calc.assert_called_once_with(today, period_months_ago)

    @patch.object(
        DatasetRankingController._ranking_controller.date_calculator,
        '_validate_and_adjust_date_range',
    )
    def test_get_year_months_with_start_year_month_and_end_year_month(
        self, mock_validate
    ):
        controller = DatasetRankingController._ranking_controller
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = None
        start_year_month = '2023-04'
        end_year_month = '2023-12'

        mock_validate.return_value = (start_year_month, end_year_month)

        result = controller.date_calculator.get_year_months(
            today, period_months_ago, start_year_month, end_year_month
        )

        assert result == (start_year_month, end_year_month)
        mock_validate.assert_called_once_with(today, start_year_month, end_year_month)


class TestDatasetRankingService:
    def _setup_common_mocks(self, mock_feedback_config, enable_org_config):
        feedback_config = mock_feedback_config.return_value
        getattr(
            feedback_config, enable_org_config
        ).get_enable_org_names.return_value = ['test_org1']
        return feedback_config

    def _get_expected_result(self):
        return [
            (
                'test_org1',
                'test_org1_title',
                'test_dataset1',
                'test_dataset1_title',
                'test_dataset1_notes',
                100,
                100,
            )
        ]

    def _assert_generic_ranking_call(
        self,
        mock_get_generic_ranking,
        top_ranked_limit,
        start_year_month,
        end_year_month,
        period_model,
        period_column,
        total_model,
        total_column,
        organization_name,
    ):
        mock_get_generic_ranking.assert_called_once_with(
            top_ranked_limit,
            start_year_month,
            end_year_month,
            period_model,
            period_column,
            total_model,
            total_column,
            enable_org=None,
            organization_name=organization_name,
        )

    def test_get_dataset_ranking_with_invalid_metric(self):
        controller = DatasetRankingController._ranking_controller

        with pytest.raises(ValidationError) as exc_info:
            controller.ranking_service.get_dataset_ranking(
                metric='invalid_metric',
                top_ranked_limit='1',
                start_year_month='2023-04',
                end_year_month='2023-12',
                organization_name=None,
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "Invalid metric specified."

    @patch('ckanext.feedback.controllers.api.ranking.config.get')
    @patch('ckanext.feedback.controllers.api.ranking.toolkit.url_for')
    def test_generate_dataset_ranking_list_with_different_metric(
        self, mock_toolkit_url_for, mock_config_get
    ):
        controller = DatasetRankingController._ranking_controller
        results = [
            (
                'test_org1',
                'test_org1_title',
                'test_dataset1',
                'test_dataset1_title',
                'test_dataset1_notes',
                100,
                100,
            )
        ]

        mock_config_get.return_value = 'https://test-site-url'
        mock_toolkit_url_for.return_value = '/dataset/test_dataset1_title'

        result_likes = controller.ranking_service.generate_dataset_ranking_list(
            results, metric_name='likes'
        )
        assert result_likes == [
            {
                'rank': 1,
                'group_name': 'test_org1',
                'group_title': 'test_org1_title',
                'dataset_title': 'test_dataset1_title',
                'dataset_notes': 'test_dataset1_notes',
                'dataset_link': 'https://test-site-url/dataset/test_dataset1_title',
                'likes_count_by_period': 100,
                'total_likes_count': 100,
            },
        ]

        result_comments = controller.ranking_service.generate_dataset_ranking_list(
            results, metric_name='resource_comments'
        )

        assert result_comments == [
            {
                'rank': 1,
                'group_name': 'test_org1',
                'group_title': 'test_org1_title',
                'dataset_title': 'test_dataset1_title',
                'dataset_notes': 'test_dataset1_notes',
                'dataset_link': 'https://test-site-url/dataset/test_dataset1_title',
                'resource_comments_count_by_period': 100,
                'total_resource_comments_count': 100,
            },
        ]

        result_utilization_comments = (
            controller.ranking_service.generate_dataset_ranking_list(
                results, metric_name='utilization_comments'
            )
        )

        assert result_utilization_comments == [
            {
                'rank': 1,
                'group_name': 'test_org1',
                'group_title': 'test_org1_title',
                'dataset_title': 'test_dataset1_title',
                'dataset_notes': 'test_dataset1_notes',
                'dataset_link': 'https://test-site-url/dataset/test_dataset1_title',
                'utilization_comments_count_by_period': 100,
                'total_utilization_comments_count': 100,
            },
        ]


class TestDatasetRankingController:
    def test_extract_parameters(self):
        controller = DatasetRankingController._ranking_controller
        data_dict = {
            'top_ranked_limit': '5',
            'period_months_ago': '3',
            'start_year_month': '2023-04',
            'end_year_month': '2023-12',
            'aggregation_metric': 'download',
            'organization_name': 'test_org1',
        }

        result = controller._extract_parameters(data_dict)

        assert result == {
            'top_ranked_limit': '5',
            'period_months_ago': '3',
            'start_year_month': '2023-04',
            'end_year_month': '2023-12',
            'aggregation_metric': 'download',
            'organization_name': 'test_org1',
        }

    def test_extract_parameters_with_defaults(self):
        controller = DatasetRankingController._ranking_controller
        data_dict = {}

        result = controller._extract_parameters(data_dict)

        assert result == {
            'top_ranked_limit': 5,
            'period_months_ago': None,
            'start_year_month': None,
            'end_year_month': None,
            'aggregation_metric': 'download',
            'organization_name': None,
        }

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    @patch.object(
        DatasetRankingController._ranking_controller.ranking_service,
        'generate_dataset_ranking_list',
    )
    @patch.object(
        DatasetRankingController._ranking_controller.ranking_service,
        'get_dataset_ranking',
    )
    @patch.object(
        DatasetRankingController._ranking_controller.validator,
        'validate_aggregation_metric',
    )
    @patch.object(
        DatasetRankingController._ranking_controller.date_calculator, 'get_year_months'
    )
    @patch.object(
        DatasetRankingController._ranking_controller.validator,
        'validate_top_ranked_limit',
    )
    @patch.object(DatasetRankingController._ranking_controller, '_extract_parameters')
    @patch.object(
        DatasetRankingController._ranking_controller.validator,
        'validate_input_parameters',
    )
    def test_get_datasets_ranking_with_download_metric(
        self,
        mock_validate_input,
        mock_extract_params,
        mock_validate_limit,
        mock_get_year_months,
        mock_validate_metric,
        mock_get_dataset_ranking,
        mock_generate_ranking_list,
    ):
        controller = DatasetRankingController._ranking_controller

        mock_validate_input.return_value = None
        mock_extract_params.return_value = {
            'top_ranked_limit': '1',
            'period_months_ago': 'all',
            'start_year_month': None,
            'end_year_month': None,
            'aggregation_metric': 'download',
            'organization_name': None,
        }
        mock_validate_limit.return_value = None
        mock_get_year_months.return_value = ('2023-04', '2023-12')
        mock_validate_metric.return_value = None
        mock_get_dataset_ranking.return_value = [
            (
                'test_org1',
                'test_org1_title',
                'test_dataset1',
                'test_dataset1_title',
                'test_dataset1_notes',
                100,
                100,
            )
        ]
        mock_generate_ranking_list.return_value = [
            {
                'rank': 1,
                'group_name': 'test_org1',
                'group_title': 'test_org1_title',
                'dataset_title': 'test_dataset1_title',
                'dataset_notes': 'test_dataset1_notes',
                'dataset_link': 'https://test-site-url/dataset/test_dataset1_title',
                'download_count_by_period': 100,
                'total_download_count': 100,
            },
        ]

        data_dict = {
            'top_ranked_limit': '1',
            'period_months_ago': 'all',
            'start_year_month': None,
            'end_year_month': None,
            'aggregation_metric': 'download',
            'organization_name': None,
        }

        result = controller.get_datasets_ranking(data_dict)

        assert result == [
            {
                'rank': 1,
                'group_name': 'test_org1',
                'group_title': 'test_org1_title',
                'dataset_title': 'test_dataset1_title',
                'dataset_notes': 'test_dataset1_notes',
                'dataset_link': 'https://test-site-url/dataset/test_dataset1_title',
                'download_count_by_period': 100,
                'total_download_count': 100,
            },
        ]

        mock_validate_input.assert_called_once_with(data_dict)
        mock_extract_params.assert_called_once_with(data_dict)
        mock_validate_limit.assert_called_once_with('1')
        mock_get_year_months.assert_called_once_with(
            datetime(2024, 1, 1, 15, 0, 0), 'all', None, None
        )
        mock_validate_metric.assert_called_once_with('download')
        mock_get_dataset_ranking.assert_called_once_with(
            metric='download',
            top_ranked_limit='1',
            start_year_month='2023-04',
            end_year_month='2023-12',
            organization_name=None,
        )
        mock_generate_ranking_list.assert_called_once_with(
            [
                (
                    'test_org1',
                    'test_org1_title',
                    'test_dataset1',
                    'test_dataset1_title',
                    'test_dataset1_notes',
                    100,
                    100,
                )
            ],
            metric_name='download',
        )

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    @patch.object(
        DatasetRankingController._ranking_controller.ranking_service,
        'get_dataset_ranking',
    )
    @patch.object(
        DatasetRankingController._ranking_controller.validator,
        'validate_aggregation_metric',
    )
    @patch.object(
        DatasetRankingController._ranking_controller.date_calculator, 'get_year_months'
    )
    @patch.object(
        DatasetRankingController._ranking_controller.validator,
        'validate_top_ranked_limit',
    )
    @patch.object(DatasetRankingController._ranking_controller, '_extract_parameters')
    @patch.object(
        DatasetRankingController._ranking_controller.validator,
        'validate_input_parameters',
    )
    def test_get_datasets_ranking_with_invalid_aggregation_metric(
        self,
        mock_validate_input,
        mock_extract_params,
        mock_validate_limit,
        mock_get_year_months,
        mock_validate_metric,
        mock_get_dataset_ranking,
    ):
        controller = DatasetRankingController._ranking_controller

        mock_validate_input.return_value = None
        mock_extract_params.return_value = {
            'top_ranked_limit': '1',
            'period_months_ago': 'all',
            'start_year_month': None,
            'end_year_month': None,
            'aggregation_metric': 'invalid_metric',
            'organization_name': None,
        }
        mock_validate_limit.return_value = None
        mock_get_year_months.return_value = ('2023-04', '2023-12')
        mock_validate_metric.return_value = None
        mock_get_dataset_ranking.side_effect = ValidationError(
            {"message": "Invalid metric specified."}
        )

        data_dict = {
            'top_ranked_limit': '1',
            'period_months_ago': 'all',
            'start_year_month': None,
            'end_year_month': None,
            'aggregation_metric': 'invalid_metric',
            'organization_name': None,
        }

        with pytest.raises(ValidationError) as exc_info:
            controller.get_datasets_ranking(data_dict)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "Invalid metric specified."

        mock_validate_input.assert_called_once_with(data_dict)
        mock_extract_params.assert_called_once_with(data_dict)
        mock_validate_limit.assert_called_once_with('1')
        mock_get_year_months.assert_called_once_with(
            datetime(2024, 1, 1, 15, 0, 0), 'all', None, None
        )
        mock_validate_metric.assert_called_once_with('invalid_metric')

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.api.ranking.'
        'dataset_ranking_service.get_generic_ranking'
    )
    @pytest.mark.parametrize(
        "metric,"
        "organization_name,"
        "validate_func,"
        "validate_org_func,"
        "period_model,"
        "period_column,"
        "total_model,"
        "total_column,"
        "enable_org_config",
        [
            (
                'download',
                None,
                'validate_download_function',
                None,
                DownloadMonthly,
                "download_count",
                DownloadSummary,
                "download",
                'download',
            ),
            (
                'likes',
                None,
                'validate_likes_function',
                None,
                ResourceLikeMonthly,
                "like_count",
                ResourceLike,
                "like_count",
                'like',
            ),
            (
                'resource_comments',
                None,
                'validate_resource_comments_function',
                None,
                ResourceCommentSummary,
                "comment",
                ResourceCommentSummary,
                "comment",
                'resource_comment',
            ),
            (
                'utilization_comments',
                None,
                'validate_utilization_comments_function',
                None,
                Utilization,
                "comment",
                Utilization,
                "comment",
                'utilization_comment',
            ),
            (
                'download',
                'test_org1',
                'validate_download_function',
                'validate_organization_download_enabled',
                DownloadMonthly,
                "download_count",
                DownloadSummary,
                "download",
                'download',
            ),
            (
                'likes',
                'test_org1',
                'validate_likes_function',
                'validate_organization_likes_enabled',
                ResourceLikeMonthly,
                "like_count",
                ResourceLike,
                "like_count",
                'like',
            ),
            (
                'resource_comments',
                'test_org1',
                'validate_resource_comments_function',
                'validate_organization_resource_comments_enabled',
                ResourceCommentSummary,
                "comment",
                ResourceCommentSummary,
                "comment",
                'resource_comment',
            ),
            (
                'utilization_comments',
                'test_org1',
                'validate_utilization_comments_function',
                'validate_organization_utilization_comments_enabled',
                Utilization,
                "comment",
                Utilization,
                "comment",
                'utilization_comment',
            ),
        ],
    )
    def test_get_dataset_ranking_parametrized(
        self,
        mock_get_generic_ranking,
        mock_feedback_config,
        metric,
        organization_name,
        validate_func,
        validate_org_func,
        period_model,
        period_column,
        total_model,
        total_column,
        enable_org_config,
    ):
        controller = DatasetRankingController._ranking_controller
        top_ranked_limit = '1'
        start_year_month = '2023-04'
        end_year_month = '2023-12'

        with patch.object(controller.validator, validate_func) as mock_validate:
            mock_validate.return_value = None

            if organization_name and validate_org_func:
                with patch.object(
                    controller.validator, 'validate_organization_name_in_group'
                ) as mock_validate_org, patch.object(
                    controller.validator, validate_org_func
                ) as mock_validate_org_func:
                    mock_validate_org.return_value = None
                    mock_validate_org_func.return_value = None

                    feedback_config = mock_feedback_config.return_value
                    getattr(
                        feedback_config, enable_org_config
                    ).get_enable_org_names.return_value = ['test_org1']

                    mock_get_generic_ranking.return_value = [
                        (
                            'test_org1',
                            'test_org1_title',
                            'test_dataset1',
                            'test_dataset1_title',
                            'test_dataset1_notes',
                            100,
                            100,
                        )
                    ]

                    result = controller.ranking_service.get_dataset_ranking(
                        metric=metric,
                        top_ranked_limit=top_ranked_limit,
                        start_year_month=start_year_month,
                        end_year_month=end_year_month,
                        organization_name=organization_name,
                    )

                    assert result == [
                        (
                            'test_org1',
                            'test_org1_title',
                            'test_dataset1',
                            'test_dataset1_title',
                            'test_dataset1_notes',
                            100,
                            100,
                        )
                    ]
                    mock_validate.assert_called_once()
                    mock_validate_org.assert_called_once_with(organization_name)
                    mock_validate_org_func.assert_called_once_with(
                        organization_name,
                        getattr(
                            feedback_config, enable_org_config
                        ).get_enable_org_names.return_value,
                    )
                    mock_get_generic_ranking.assert_called_once_with(
                        top_ranked_limit,
                        start_year_month,
                        end_year_month,
                        period_model,
                        period_column,
                        total_model,
                        total_column,
                        enable_org=None,
                        organization_name=organization_name,
                    )
            else:
                feedback_config = mock_feedback_config.return_value
                getattr(
                    feedback_config, enable_org_config
                ).get_enable_org_names.return_value = ['test_org1']

                mock_get_generic_ranking.return_value = [
                    (
                        'test_org1',
                        'test_org1_title',
                        'test_dataset1',
                        'test_dataset1_title',
                        'test_dataset1_notes',
                        100,
                        100,
                    )
                ]

                result = controller.ranking_service.get_dataset_ranking(
                    metric=metric,
                    top_ranked_limit=top_ranked_limit,
                    start_year_month=start_year_month,
                    end_year_month=end_year_month,
                    organization_name=organization_name,
                )

                assert result == [
                    (
                        'test_org1',
                        'test_org1_title',
                        'test_dataset1',
                        'test_dataset1_title',
                        'test_dataset1_notes',
                        100,
                        100,
                    )
                ]
                mock_validate.assert_called_once()
                mock_get_generic_ranking.assert_called_once_with(
                    top_ranked_limit,
                    start_year_month,
                    end_year_month,
                    period_model,
                    period_column,
                    total_model,
                    total_column,
                    enable_org=None,
                    organization_name=organization_name,
                )
