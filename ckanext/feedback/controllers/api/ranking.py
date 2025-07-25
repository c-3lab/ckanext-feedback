import logging
import re
from dataclasses import dataclass
from datetime import datetime

from ckan.common import config
from ckan.logic import side_effect_free
from ckan.plugins import toolkit
from dateutil.relativedelta import relativedelta

import ckanext.feedback.services.ranking.dataset as dataset_ranking_service
from ckanext.feedback.services.common.config import FeedbackConfig
from ckanext.feedback.services.organization import organization as organization_service

log = logging.getLogger(__name__)


@dataclass
class RankingConfig:
    VALID_PARAMETERS = [
        'top_ranked_limit',
        'period_months_ago',
        'start_year_month',
        'end_year_month',
        'aggregation_metric',
        'organization_name',
    ]
    TOP_RANKED_LIMIT_DEFAULT = 5
    TOP_RANKED_LIMIT_MIN = 1
    TOP_RANKED_LIMIT_MAX = 100
    DATE_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"  # Format YYYY-MM
    PERIOD_ALL = 'all'
    START_YEAR_MONTH_DEFAULT = '2023-04'
    AGGREGATION_METRIC_DEFAULT = 'download'
    AGGREGATION_METRIC_LIST = [
        'download',
    ]


class RankingValidator:
    def __init__(self, config: RankingConfig):
        self.config = config

    def validate_input_parameters(self, data_dict):
        invalid_keys = [
            key for key in data_dict.keys() if key not in self.config.VALID_PARAMETERS
        ]

        if invalid_keys:
            raise toolkit.ValidationError(
                {
                    "message": (
                        f"The following fields are not valid: {invalid_keys}. "
                        "Please review the provided input and ensure only these fields "
                        f"are included: {self.config.VALID_PARAMETERS}."
                    )
                }
            )

    def validate_top_ranked_limit(self, top_ranked_limit):
        try:
            top_ranked_limit = int(top_ranked_limit)
        except ValueError:
            raise toolkit.ValidationError(
                {"message": "The 'top_ranked_limit' must be a number."}
            )

        if not (
            self.config.TOP_RANKED_LIMIT_MIN
            <= int(top_ranked_limit)
            <= self.config.TOP_RANKED_LIMIT_MAX
        ):
            raise toolkit.ValidationError(
                {
                    "message": (
                        "The 'top_ranked_limit' must be between "
                        f"{self.config.TOP_RANKED_LIMIT_MIN} and "
                        f"{self.config.TOP_RANKED_LIMIT_MAX}."
                    )
                }
            )

    def validate_date_format(self, date_str, field_name):
        if not re.match(self.config.DATE_PATTERN, date_str):
            raise toolkit.ValidationError(
                {
                    "message": (
                        f"Invalid format for '{field_name}'. "
                        "Expected format is YYYY-MM."
                    )
                }
            )

    def validate_start_year_month_not_before_default(self, start_year_month):
        if start_year_month < self.config.START_YEAR_MONTH_DEFAULT:
            raise toolkit.ValidationError(
                {
                    "message": (
                        "The start date must be later than "
                        f"{self.config.START_YEAR_MONTH_DEFAULT}."
                    )
                }
            )

    def validate_end_year_month_not_in_future(self, today, end_year_month):
        if end_year_month >= today.strftime('%Y-%m'):
            raise toolkit.ValidationError(
                {"message": "The selected period cannot be in the future."}
            )

    def validate_period_months_ago(self, today, period_months_ago):
        try:
            period = int(period_months_ago)
        except ValueError:
            raise toolkit.ValidationError(
                {
                    "message": (
                        "The period must be specified as a numerical value or "
                        f"{self.config.PERIOD_ALL}."
                    )
                }
            )

        if period <= 0:
            raise toolkit.ValidationError(
                {
                    "message": (
                        "The period must be a positive integer (natural number) "
                        "of 1 or greater."
                    )
                }
            )

        if (today - relativedelta(months=period)).strftime(
            "%Y-%m"
        ) < self.config.START_YEAR_MONTH_DEFAULT:
            raise toolkit.ValidationError(
                {
                    "message": (
                        "The selected period is beyond the allowable range. "
                        "Only periods up to "
                        f"{self.config.START_YEAR_MONTH_DEFAULT} are allowed."
                    )
                }
            )

    def validate_aggregation_metric(self, aggregation_metric):
        if aggregation_metric not in self.config.AGGREGATION_METRIC_LIST:
            raise toolkit.ValidationError(
                {"message": "This is a non-existent aggregation metric."}
            )

    def validate_download_function(self):
        if not FeedbackConfig().download.is_enable():
            raise toolkit.ValidationError(
                {
                    "message": (
                        "Download function is off. "
                        "Please contact the site administrator for assistance."
                    )
                }
            )

    def validate_organization_name_in_group(self, organization_name):
        org_name = organization_service.get_organization_name_by_name(organization_name)

        if not org_name:
            raise toolkit.ValidationError(
                {
                    "message": (
                        "The specified organization does not exist or "
                        "may have been deleted. Please enter a valid organization name."
                    )
                }
            )

    def validate_organization_download_enabled(self, organization_name, enable_orgs):
        if organization_name not in enable_orgs:
            raise toolkit.ValidationError(
                {
                    "message": (
                        "An organization with the download feature disabled "
                        "has been selected. "
                        "Please contact the site administrator for assistance."
                    )
                }
            )


class DateRangeCalculator:
    def __init__(self, config: RankingConfig, validator: RankingValidator):
        self.config = config
        self.validator = validator

    def get_year_months(
        self, today, period_months_ago, start_year_month, end_year_month
    ):
        if not period_months_ago:
            return self._validate_and_adjust_date_range(
                today, start_year_month, end_year_month
            )

        return self._calculate_date_range_from_period(today, period_months_ago)

    def _validate_and_adjust_date_range(self, today, start_year_month, end_year_month):
        if start_year_month:
            self.validator.validate_date_format(start_year_month, 'start_year_month')
            self.validator.validate_start_year_month_not_before_default(
                start_year_month
            )
        else:
            start_year_month = self.config.START_YEAR_MONTH_DEFAULT

        if end_year_month:
            self.validator.validate_date_format(end_year_month, 'end_year_month')
            self.validator.validate_end_year_month_not_in_future(today, end_year_month)
        else:
            end_year_month = (today - relativedelta(months=1)).strftime("%Y-%m")

        return start_year_month, end_year_month

    def _calculate_date_range_from_period(self, today, period_months_ago):
        end_year_month = (today - relativedelta(months=1)).strftime("%Y-%m")

        if period_months_ago == self.config.PERIOD_ALL:
            return self.config.START_YEAR_MONTH_DEFAULT, end_year_month

        self.validator.validate_period_months_ago(today, period_months_ago)

        start_year_month = (
            today - relativedelta(months=int(period_months_ago))
        ).strftime("%Y-%m")

        return start_year_month, end_year_month


class DatasetRankingService:
    def __init__(self, config: RankingConfig, validator: RankingValidator):
        self.config = config
        self.validator = validator

    def get_dataset_download_ranking(
        self, top_ranked_limit, start_year_month, end_year_month, organization_name
    ):
        self.validator.validate_download_function()

        if not FeedbackConfig().is_feedback_config_file:
            return dataset_ranking_service.get_download_ranking(
                top_ranked_limit, start_year_month, end_year_month
            )

        enable_orgs = FeedbackConfig().download.get_enable_org_names()

        if not organization_name:
            return dataset_ranking_service.get_download_ranking(
                top_ranked_limit, start_year_month, end_year_month, enable_orgs
            )

        self.validator.validate_organization_name_in_group(organization_name)
        self.validator.validate_organization_download_enabled(
            organization_name, enable_orgs
        )

        return dataset_ranking_service.get_download_ranking(
            top_ranked_limit, start_year_month, end_year_month, [organization_name]
        )

    def generate_dataset_ranking_list(self, results):
        dataset_ranking_list = []

        for index, (
            group_name,
            group_title,
            dataset_name,
            dataset_title,
            dataset_notes,
            download_count_by_period,
            total_download_count,
        ) in enumerate(results):
            site_url = config.get('ckan.site_url', '')
            dataset_path = toolkit.url_for('dataset.read', id=dataset_name)
            dataset_link = f"{site_url}{dataset_path}"

            dataset_ranking_dict = {
                'rank': index + 1,
                'group_name': group_name,
                'group_title': group_title,
                'dataset_title': dataset_title,
                'dataset_notes': dataset_notes,
                'dataset_link': dataset_link,
                'download_count_by_period': download_count_by_period,
                'total_download_count': total_download_count,
            }

            dataset_ranking_list.append(dataset_ranking_dict)

        return dataset_ranking_list


class DatasetRankingController:
    def __init__(self):
        self.config = RankingConfig()
        self.validator = RankingValidator(self.config)
        self.date_calculator = DateRangeCalculator(self.config, self.validator)
        self.ranking_service = DatasetRankingService(self.config, self.validator)

    def get_datasets_ranking(self, data_dict):
        self.validator.validate_input_parameters(data_dict)

        params = self._extract_parameters(data_dict)

        self.validator.validate_top_ranked_limit(params['top_ranked_limit'])

        today = datetime.now()
        start_year_month, end_year_month = self.date_calculator.get_year_months(
            today,
            params['period_months_ago'],
            params['start_year_month'],
            params['end_year_month'],
        )

        self.validator.validate_aggregation_metric(params['aggregation_metric'])

        if params['aggregation_metric'] == 'download':
            results = self.ranking_service.get_dataset_download_ranking(
                params['top_ranked_limit'],
                start_year_month,
                end_year_month,
                params['organization_name'],
            )

            return self.ranking_service.generate_dataset_ranking_list(results)

        return []

    def _extract_parameters(self, data_dict):
        return {
            'top_ranked_limit': data_dict.get(
                'top_ranked_limit', self.config.TOP_RANKED_LIMIT_DEFAULT
            ),
            'period_months_ago': data_dict.get('period_months_ago'),
            'start_year_month': data_dict.get('start_year_month'),
            'end_year_month': data_dict.get('end_year_month'),
            'aggregation_metric': data_dict.get(
                'aggregation_metric', self.config.AGGREGATION_METRIC_DEFAULT
            ),
            'organization_name': data_dict.get('organization_name'),
        }


_ranking_controller = DatasetRankingController()


@side_effect_free
def datasets_ranking(context, data_dict):
    return _ranking_controller.get_datasets_ranking(data_dict)
