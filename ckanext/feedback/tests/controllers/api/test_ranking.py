import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from ckan import model
from ckan.plugins.toolkit import ValidationError

from ckanext.feedback.command.feedback import (
    create_download_monthly_tables,
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.api import ranking as DatasetRankingController

log = logging.getLogger(__name__)


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestRankingApi:
    def setup_class(cls):
        model.repo.init_db()
        engine = model.meta.engine
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)
        create_download_monthly_tables(engine)

    @patch('ckanext.feedback.controllers.api.ranking.get_year_months')
    @patch('ckanext.feedback.controllers.api.ranking.get_dataset_download_ranking')
    @patch('ckanext.feedback.controllers.api.ranking.generate_dataset_ranking_list')
    def test_datasets_ranking(
        self,
        mock_generate_list,
        mock_get_ranking,
        mock_get_year_months,
    ):
        mock_get_year_months.return_value = ('2006-10', '2023-12')
        mock_get_ranking.return_value = [
            (
                'group_name1',
                'group_title1',
                'dataset_name1',
                'dataset_title1',
                'dataset_notes1',
                100,
                100,
            )
        ]
        mock_generate_list.return_value = [
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

    @patch('ckanext.feedback.controllers.api.ranking.validate_aggregation_metric')
    def test_datasets_ranking_aggregation_metric_validation(
        self, mock_validate_aggregation_metric
    ):
        context = {}
        data_dict = {
            'top_ranked_limit': '5',
            'period_months_ago': 'all',
            'start_year_month': None,
            'end_year_month': None,
            'aggregation_metric': 'comment',
            'organization_name': None,
        }

        DatasetRankingController.datasets_ranking(context, data_dict)

        mock_validate_aggregation_metric.assert_called_once_with(
            'comment', ['download']
        )

    def test_validate_input_parameters(self):
        data_dict = {'test_parameter': '10'}

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_input_parameters(data_dict)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "The following fields are not valid: ['test_parameter']. "
            "Please review the provided input and ensure only these fields "
            "are included: ['top_ranked_limit', 'period_months_ago', "
            "'start_year_month', 'end_year_month', "
            "'aggregation_metric', 'organization_name']."
        )

    @patch('ckanext.feedback.controllers.api.ranking.validate_and_adjust_date_range')
    def test_get_year_months(self, mock_validate_and_adjust_date_range):
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = None
        start_year_month_input = '2023-04'
        end_year_month_input = '2023-12'

        mock_validate_and_adjust_date_range.return_value = ('2023-04', '2023-12')

        result = DatasetRankingController.get_year_months(
            today, period_months_ago, start_year_month_input, end_year_month_input
        )

        assert result == ('2023-04', '2023-12')

    def test_validate_and_adjust_date_range_full_input(self):
        today = datetime(2024, 1, 1, 15, 0, 0)
        start_year_month = '2023-04'
        end_year_month = '2023-12'

        result = DatasetRankingController.validate_and_adjust_date_range(
            today, start_year_month, end_year_month
        )

        assert result == ('2023-04', '2023-12')

    def test_validate_and_adjust_date_range_default_start_date(self):
        today = datetime(2024, 1, 1, 15, 0, 0)
        start_year_month = None
        end_year_month = '2023-12'

        result = DatasetRankingController.validate_and_adjust_date_range(
            today, start_year_month, end_year_month
        )

        assert result == ('2023-04', '2023-12')

    def test_validate_and_adjust_date_range_default_end_date(self):
        today = datetime(2024, 1, 1, 15, 0, 0)
        start_year_month = '2023-04'
        end_year_month = None

        result = DatasetRankingController.validate_and_adjust_date_range(
            today, start_year_month, end_year_month
        )

        assert result == ('2023-04', '2023-12')

    def test_calculate_date_range_from_period_correct_range(self):
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = '3'

        result = DatasetRankingController.calculate_date_range_from_period(
            today, period_months_ago
        )

        assert result == ('2023-10', '2023-12')

    @patch('ckanext.feedback.controllers.api.ranking.validate_period_months_ago')
    def test_calculate_date_range_from_period_validation_called(
        self, mock_validate_period_months_ago
    ):
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = '0'

        DatasetRankingController.calculate_date_range_from_period(
            today, period_months_ago
        )

        mock_validate_period_months_ago.assert_called_once_with(
            today, period_months_ago
        )

    @patch('ckanext.feedback.controllers.api.ranking.config.get')
    @patch(
        'ckanext.feedback.controllers.api.ranking.'
        'dataset_ranking_service.get_download_ranking'
    )
    def test_get_dataset_download_ranking_with_feedback_config_and_organization(
        self, mock_get_download_ranking, mock_config_get
    ):
        is_feedback_config = True
        top_ranked_limit = '5'
        start_year_month = '2023-04'
        end_year_month = '2023-12'
        organization_name = None

        mock_config_get.return_value = ['group_name1']
        mock_get_download_ranking.return_value = [
            (
                'group_name1',
                'group_title1',
                'dataset_name1',
                'dataset_title1',
                'dataset_notes1',
                100,
                100,
            )
        ]

        result = DatasetRankingController.get_dataset_download_ranking(
            is_feedback_config,
            top_ranked_limit,
            start_year_month,
            end_year_month,
            organization_name,
        )

        assert result == [
            (
                'group_name1',
                'group_title1',
                'dataset_name1',
                'dataset_title1',
                'dataset_notes1',
                100,
                100,
            )
        ]

    @patch('ckanext.feedback.controllers.api.ranking.config.get')
    @patch(
        'ckanext.feedback.controllers.api.ranking.'
        'dataset_ranking_service.get_download_ranking'
    )
    @patch(
        'ckanext.feedback.controllers.api.ranking.validate_organization_name_in_group'
    )
    def test_get_dataset_download_ranking_with_organization(
        self,
        mock_validate_organization_name_in_group,
        mock_get_download_ranking,
        mock_config_get,
    ):
        is_feedback_config = True
        top_ranked_limit = '5'
        start_year_month = '2023-04'
        end_year_month = '2023-12'
        organization_name = 'group_name2'

        mock_config_get.return_value = ['group_name1', 'group_name2']
        mock_get_download_ranking.return_value = [
            (
                'group_name2',
                'group_title2',
                'dataset_name2',
                'dataset_title2',
                'dataset_notes2',
                200,
                200,
            )
        ]
        mock_validate_organization_name_in_group.return_value = None

        result = DatasetRankingController.get_dataset_download_ranking(
            is_feedback_config,
            top_ranked_limit,
            start_year_month,
            end_year_month,
            organization_name,
        )

        assert result == [
            (
                'group_name2',
                'group_title2',
                'dataset_name2',
                'dataset_title2',
                'dataset_notes2',
                200,
                200,
            )
        ]

    @patch(
        'ckanext.feedback.controllers.api.ranking.'
        'dataset_ranking_service.get_download_ranking'
    )
    def test_get_dataset_download_ranking_without_feedback_config(
        self, mock_get_download_ranking
    ):
        is_feedback_config = False
        top_ranked_limit = '5'
        start_year_month = '2023-04'
        end_year_month = '2023-12'
        organization_name = None

        mock_get_download_ranking.return_value = [
            (
                'group_name1',
                'group_title1',
                'dataset_name1',
                'dataset_title1',
                'dataset_notes1',
                100,
                100,
            )
        ]

        result = DatasetRankingController.get_dataset_download_ranking(
            is_feedback_config,
            top_ranked_limit,
            start_year_month,
            end_year_month,
            organization_name,
        )

        assert result == [
            (
                'group_name1',
                'group_title1',
                'dataset_name1',
                'dataset_title1',
                'dataset_notes1',
                100,
                100,
            )
        ]

    @patch('ckanext.feedback.controllers.api.ranking.config.get')
    @patch('ckanext.feedback.controllers.api.ranking.toolkit.url_for')
    def test_generate_dataset_ranking_list(self, mock_toolkit_url_for, mock_config_get):
        dataset_ranking_list = []
        results = [
            (
                'group_name1',
                'group_title1',
                'dataset_name1',
                'dataset_title1',
                'dataset_notes1',
                100,
                100,
            )
        ]

        mock_config_get.return_value = 'https://test-site-url'
        mock_toolkit_url_for.return_value = '/dataset/dataset-title1'

        result = DatasetRankingController.generate_dataset_ranking_list(
            dataset_ranking_list, results
        )

        assert result == [
            {
                'rank': 1,
                'group_name': 'group_name1',
                'group_title': 'group_title1',
                'dataset_title': 'dataset_title1',
                'dataset_notes': 'dataset_notes1',
                'dataset_link': 'https://test-site-url/dataset/dataset-title1',
                'download_count_by_period': 100,
                'total_download_count': 100,
            },
        ]

    def test_validate_top_ranked_limit(self):
        top_ranked_limit = '0'

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_top_ranked_limit(top_ranked_limit)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "The 'top_ranked_limit' must be between 1 and 100."

    def test_validate_period_input(self):
        period_months_ago = None
        start_year_month_input = None
        end_year_month_input = None

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_period_input(
                period_months_ago, start_year_month_input, end_year_month_input
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "Please set the period for aggregation."

    def test_validate_start_year_month_format(self):
        pattern = r"^\d{4}-(0[1-9]|1[0-2])$"
        start_year_month = '2024-1'

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_start_year_month_format(
                pattern, start_year_month
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == "Invalid format for 'start_year_month'. Expected format is YYYY-MM."
        )

    def test_validate_start_year_month_not_before_default(self):
        START_YEAR_MONTH_DEFAULT = '2023-04'
        start_year_month = '2023-03'

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_start_year_month_not_before_default(
                START_YEAR_MONTH_DEFAULT, start_year_month
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == f"The start date must be later than {START_YEAR_MONTH_DEFAULT}."
        )

    def test_validate_end_year_month_format(self):
        pattern = r"^\d{4}-(0[1-9]|1[0-2])$"
        end_year_month = '2024-1'

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_end_year_month_format(
                pattern, end_year_month
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == "Invalid format for 'end_year_month'. Expected format is YYYY-MM."
        )

    def test_validate_end_year_month_not_in_future(self):
        today = datetime(2024, 1, 1, 15, 0, 0)
        end_year_month = '2024-02'

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_end_year_month_not_in_future(
                today, end_year_month
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "The selected period cannot be in the future."

    def test_validate_period_months_ago(self):
        today = datetime(2024, 1, 1, 15, 0, 0)
        period_months_ago = '0'

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_period_months_ago(
                today, period_months_ago
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "The selected period is beyond the allowable range. "
            "Only periods up to 2023-04 are allowed."
        )

    def test_validate_enable_orgs_in_config(self):
        enable_orgs = None

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_enable_orgs_in_config(enable_orgs)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == "There are no organizations with the download feature enabled. "
            "Please contact the site administrator for assistance."
        )

    @patch('ckanext.feedback.controllers.api.ranking.get_group_service.get_group_names')
    def test_validate_organization_name_in_group_with_invalid_name(
        self, mock_get_group_names
    ):
        organization_name = 'group_name2'

        mock_get_group_names.return_value = []

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_organization_name_in_group(
                organization_name
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "The specified organization does not exist or "
            "may have been deleted. Please enter a valid organization name."
        )

    @patch('ckanext.feedback.controllers.api.ranking.get_group_service.get_group_names')
    def test_validate_organization_name_in_group_with_valid_name(
        self, mock_get_group_names
    ):
        organization_name = 'group_name2'

        mock_get_group_names.return_value = ['group_name2']

        DatasetRankingController.validate_organization_name_in_group(organization_name)

    def test_validate_organization_download_enabled_with_disabled_organization(self):
        organization_name = 'test_org3'
        enable_org = ['test_org1', 'test_org2']

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_organization_download_enabled(
                organization_name, enable_org
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message
            == "A organization with the download feature disabled has been selected. "
            "Please contact the site administrator for assistance."
        )

    def test_validate_organization_download_enabled_with_enabled_organization(self):
        organization_name = 'test_org3'
        enable_org = ['test_org1', 'test_org2', 'test_org3']

        DatasetRankingController.validate_organization_download_enabled(
            organization_name, enable_org
        )

    @patch('ckanext.feedback.controllers.api.ranking.FeedbackConfig')
    def test_validate_download_function(self, mock_feedback_config):
        is_feedback_config = False

        mock_download = MagicMock()
        mock_download.is_enable.return_value = False
        mock_feedback_config.return_value.download = mock_download

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_download_function(is_feedback_config)

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert (
            error_message == "Download function is off. "
            "Please contact the site administrator for assistance."
        )

    def test_validate_aggregation_metric(self):
        aggregation_metric = 'test'
        aggregation_metric_list = ['download', 'comment']

        with pytest.raises(ValidationError) as exc_info:
            DatasetRankingController.validate_aggregation_metric(
                aggregation_metric, aggregation_metric_list
            )

        error_dict = exc_info.value.__dict__.get('error_dict')
        error_message = error_dict.get('message')

        assert error_message == "This is a non-existent aggregation metric."
