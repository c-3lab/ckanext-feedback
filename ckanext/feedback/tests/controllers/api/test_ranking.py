from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from ckan.plugins.toolkit import ValidationError

from ckanext.feedback.controllers.api import ranking as DatasetRankingController


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
        aggregation_metric = 'download'

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
    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    @patch('ckanext.feedback.controllers.api.ranking.dataset_ranking_service')
    @patch.object(
        DatasetRankingController._ranking_controller.validator,
        'validate_organization_download_enabled',
    )
    @patch.object(
        DatasetRankingController._ranking_controller.validator,
        'validate_organization_name_in_group',
    )
    @patch.object(
        DatasetRankingController._ranking_controller.validator,
        'validate_download_function',
    )
    def test_get_dataset_download_ranking_with_feedback_config(
        self,
        mock_validate_download,
        mock_validate_org,
        mock_validate_org_download,
        mock_dataset_ranking_service,
        mock_feedback_config,
    ):
        controller = DatasetRankingController._ranking_controller
        top_ranked_limit = '1'
        start_year_month = '2023-04'
        end_year_month = '2023-12'
        organization_name = 'test_org1'

        mock_validate_download.return_value = None
        mock_validate_org.return_value = None
        mock_validate_org_download.return_value = None

        feedback_config = mock_feedback_config.return_value
        feedback_config.is_feedback_config_file = True
        feedback_config.download.get_enable_org_names.return_value = ['test_org1']

        mock_dataset_ranking_service.get_download_ranking.return_value = [
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

        result = controller.ranking_service.get_dataset_download_ranking(
            top_ranked_limit,
            start_year_month,
            end_year_month,
            organization_name,
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

        mock_validate_download.assert_called_once()
        mock_validate_org.assert_called_once_with(organization_name)
        mock_validate_org_download.assert_called_once_with(
            organization_name, ['test_org1']
        )
        mock_dataset_ranking_service.get_download_ranking.assert_called_once_with(
            top_ranked_limit, start_year_month, end_year_month, [organization_name]
        )

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    @patch('ckanext.feedback.controllers.api.ranking.dataset_ranking_service')
    @patch.object(
        DatasetRankingController._ranking_controller.validator,
        'validate_download_function',
    )
    def test_get_dataset_download_ranking_without_organization_name(
        self, mock_validate_download, mock_dataset_ranking_service, mock_feedback_config
    ):
        controller = DatasetRankingController._ranking_controller
        top_ranked_limit = '1'
        start_year_month = '2023-04'
        end_year_month = '2023-12'
        organization_name = None

        mock_validate_download.return_value = None

        mock_feedback_config.return_value.is_feedback_config_file = True
        mock_feedback_config.return_value.download.get_enable_org_names.return_value = [
            'test_org1'
        ]

        mock_dataset_ranking_service.get_download_ranking.return_value = [
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

        result = controller.ranking_service.get_dataset_download_ranking(
            top_ranked_limit,
            start_year_month,
            end_year_month,
            organization_name,
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

        mock_validate_download.assert_called_once()
        mock_dataset_ranking_service.get_download_ranking.assert_called_once_with(
            top_ranked_limit, start_year_month, end_year_month, ['test_org1']
        )

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    @patch('ckanext.feedback.controllers.api.ranking.dataset_ranking_service')
    @patch.object(
        DatasetRankingController._ranking_controller.validator,
        'validate_download_function',
    )
    def test_get_dataset_download_ranking_without_feedback_config(
        self, mock_validate_download, mock_dataset_ranking_service, mock_feedback_config
    ):
        controller = DatasetRankingController._ranking_controller
        top_ranked_limit = '1'
        start_year_month = '2023-04'
        end_year_month = '2023-12'
        organization_name = None

        mock_validate_download.return_value = None

        mock_feedback_config.return_value.is_feedback_config_file = False

        mock_dataset_ranking_service.get_download_ranking.return_value = [
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

        result = controller.ranking_service.get_dataset_download_ranking(
            top_ranked_limit,
            start_year_month,
            end_year_month,
            organization_name,
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

        mock_validate_download.assert_called_once()
        mock_dataset_ranking_service.get_download_ranking.assert_called_once_with(
            top_ranked_limit, start_year_month, end_year_month
        )

    @patch('ckanext.feedback.controllers.api.ranking.config.get')
    @patch('ckanext.feedback.controllers.api.ranking.toolkit.url_for')
    def test_generate_dataset_ranking_list(self, mock_toolkit_url_for, mock_config_get):
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

        result = controller.ranking_service.generate_dataset_ranking_list(results)

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
        'get_dataset_download_ranking',
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
    def test_get_datasets_ranking_with_download_aggregation_metric(
        self,
        mock_validate_input,
        mock_extract_params,
        mock_validate_limit,
        mock_get_year_months,
        mock_validate_metric,
        mock_get_download_ranking,
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
        mock_get_download_ranking.return_value = [
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
        mock_get_download_ranking.assert_called_once_with(
            '1', '2023-04', '2023-12', None
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
            ]
        )

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
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

        data_dict = {
            'top_ranked_limit': '1',
            'period_months_ago': 'all',
            'start_year_month': None,
            'end_year_month': None,
            'aggregation_metric': 'invalid_metric',
            'organization_name': None,
        }

        result = controller.get_datasets_ranking(data_dict)

        assert result == []

        mock_validate_input.assert_called_once_with(data_dict)
        mock_extract_params.assert_called_once_with(data_dict)
        mock_validate_limit.assert_called_once_with('1')
        mock_get_year_months.assert_called_once_with(
            datetime(2024, 1, 1, 15, 0, 0), 'all', None, None
        )
        mock_validate_metric.assert_called_once_with('invalid_metric')
