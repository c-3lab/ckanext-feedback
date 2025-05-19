import logging
import re
from datetime import datetime

from ckan.common import config
from ckan.logic import side_effect_free
from ckan.plugins import toolkit
from dateutil.relativedelta import relativedelta

import ckanext.feedback.services.group.get as get_group_service
import ckanext.feedback.services.ranking.dataset as dataset_ranking_service
from ckanext.feedback.services.common.config import FeedbackConfig

log = logging.getLogger(__name__)


# Default constants
TOP_RANKED_LIMIT_DEFAULT = 5
PERIOD_MONTHS_AGO_ALL = 'all'
START_YEAR_MONTH_DEFAULT = '2023-04'
AGGREGATION_METRIC_DOWNLOAD = 'download'


@side_effect_free
def datasets_ranking(context, data_dict):
    """
    Fetch and return a ranking of datasets based on download counts
    or other aggregation metrics for a given period and conditions.
    """
    # Raise an error if the provided parameter is invalid
    validate_input_parameters(data_dict)

    # Retrieve input values or use defaults
    top_ranked_limit = data_dict.get('top_ranked_limit', TOP_RANKED_LIMIT_DEFAULT)
    period_months_ago = data_dict.get('period_months_ago')
    start_year_month_input = data_dict.get('start_year_month')
    end_year_month_input = data_dict.get('end_year_month')
    aggregation_metric = data_dict.get(
        'aggregation_metric', AGGREGATION_METRIC_DOWNLOAD
    )
    organization_name = data_dict.get('organization_name')

    # Ensure 'top_ranked_limit' is between 1 and 100
    validate_top_ranked_limit(top_ranked_limit)

    # Validate the input for aggregation period
    validate_period_input(
        period_months_ago, start_year_month_input, end_year_month_input
    )

    # Define the list of valid aggregation metrics
    aggregation_metric_list = [AGGREGATION_METRIC_DOWNLOAD]

    # Validate that the aggregation metric is valid
    validate_aggregation_metric(aggregation_metric, aggregation_metric_list)

    today = datetime.now()

    # Determine start and end year-month based on input or defaults
    start_year_month, end_year_month = get_year_months(
        today, period_months_ago, start_year_month_input, end_year_month_input
    )

    # Check if feedback configuration file exists
    is_feedback_config = FeedbackConfig().is_feedback_config_file

    dataset_ranking_list = []

    if aggregation_metric == AGGREGATION_METRIC_DOWNLOAD:
        # Get dataset download ranking data
        results = get_dataset_download_ranking(
            is_feedback_config,
            top_ranked_limit,
            start_year_month,
            end_year_month,
            organization_name,
        )

        # Format and append results to the ranking list
        dataset_ranking_list = generate_dataset_ranking_list(
            dataset_ranking_list, results
        )

    return dataset_ranking_list


def validate_input_parameters(data_dict):
    parameter_list = [
        'top_ranked_limit',
        'period_months_ago',
        'start_year_month',
        'end_year_month',
        'aggregation_metric',
        'organization_name',
    ]

    invalid_keys = [key for key in data_dict.keys() if key not in parameter_list]

    if invalid_keys:
        raise toolkit.ValidationError(
            {
                "message": (
                    f"The following fields are not valid: {invalid_keys}. "
                    "Please review the provided input and ensure only these fields "
                    f"are included: {parameter_list}."
                )
            }
        )


def get_year_months(
    today, period_months_ago, start_year_month_input, end_year_month_input
):
    """
    Calculate start and end year-months based on input period or specific date range.
    """
    if not period_months_ago:
        # Use provided start and end year-month, validate and adjust as needed
        start_year_month, end_year_month = validate_and_adjust_date_range(
            today, start_year_month_input, end_year_month_input
        )
        return start_year_month, end_year_month

    # Calculate date range based on period in months
    start_year_month, end_year_month = calculate_date_range_from_period(
        today, period_months_ago
    )
    return start_year_month, end_year_month


def validate_and_adjust_date_range(today, start_year_month, end_year_month):
    """
    Validate the format of start and end year-month inputs and adjust as necessary.
    """
    pattern = r"^\d{4}-(0[1-9]|1[0-2])$"  # Format YYYY-MM

    if start_year_month:
        # Validate the format of start_year_month
        validate_start_year_month_format(pattern, start_year_month)
        validate_start_year_month_not_before_default(
            START_YEAR_MONTH_DEFAULT, start_year_month
        )

    if end_year_month:
        # Validate the format of end_year_month
        validate_end_year_month_format(pattern, end_year_month)
        # Validate that the selected end_year_month is not in the future
        validate_end_year_month_not_in_future(today, end_year_month)

    # If only start_year_month is provided, set end_year_month to the last month
    if start_year_month and not end_year_month:
        end_year_month = (today - relativedelta(months=1)).strftime("%Y-%m")

    # If only end_year_month is provided, set start_year_month to default value
    if not start_year_month and end_year_month:
        start_year_month = START_YEAR_MONTH_DEFAULT

    return start_year_month, end_year_month


def calculate_date_range_from_period(today, period_months_ago):
    """
    Calculate start and end year-months based on the given number of months ago.
    """
    # Validate that the period is within allowed values
    validate_period_months_ago(today, period_months_ago)

    # Default start year-month
    tmp_start_year_month = START_YEAR_MONTH_DEFAULT

    # Calculate start year-month based on period if numeric
    if period_months_ago != PERIOD_MONTHS_AGO_ALL:
        tmp_start_year_month = (
            today - relativedelta(months=int(period_months_ago))
        ).strftime("%Y-%m")

    start_year_month = tmp_start_year_month
    # End year-month is always set to the last month
    end_year_month = (today - relativedelta(months=1)).strftime("%Y-%m")

    return start_year_month, end_year_month


def get_dataset_download_ranking(
    is_feedback_config,
    top_ranked_limit,
    start_year_month,
    end_year_month,
    organization_name,
):
    """
    Retrieve dataset download ranking data based on input parameters.
    """
    # Raise an error if download functionality is off and feedback config is missing
    validate_download_function(is_feedback_config)

    # Check if the organization_name exists in the GROUP table
    validate_organization_name_in_group(organization_name)

    enable_orgs = [organization_name]

    if is_feedback_config:
        # Load the list of organizations with download feature enabled
        enable_orgs_in_config = FeedbackConfig().download.get_enable_orgs()

        # Validate the existence of enabled organizations
        validate_enable_orgs_in_config(enable_orgs_in_config)

        if organization_name:
            # Ensure the organization has downloads enabled
            validate_organization_download_enabled(
                organization_name, enable_orgs_in_config
            )
        else:
            enable_orgs = enable_orgs_in_config

    # Fetch dataset ranking based on downloads
    return dataset_ranking_service.get_download_ranking(
        top_ranked_limit,
        start_year_month,
        end_year_month,
        enable_orgs,
    )


def generate_dataset_ranking_list(dataset_ranking_list, results):
    """
    Generate a list of datasets with their ranking details.
    """
    for index, (
        group_name,
        group_title,
        dataset_name,
        dataset_title,
        dataset_notes,
        download_count_by_period,
        total_download_count,
    ) in enumerate(results):
        # Construct the dataset URL
        site_url = config.get('ckan.site_url', '')
        dataset_path = toolkit.url_for('dataset.read', id=dataset_name)
        dataset_link = f"{site_url}{dataset_path}"

        # Format ranking data into a dictionary
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

        # Add to the ranking list
        dataset_ranking_list.append(dataset_ranking_dict)

    return dataset_ranking_list


def validate_top_ranked_limit(top_ranked_limit):
    if not (1 <= int(top_ranked_limit) <= 100):
        raise toolkit.ValidationError(
            {"message": "The 'top_ranked_limit' must be between 1 and 100."}
        )


def validate_period_input(
    period_months_ago, start_year_month_input, end_year_month_input
):
    if (
        not period_months_ago
        and not start_year_month_input
        and not end_year_month_input
    ):
        raise toolkit.ValidationError(
            {"message": "Please set the period for aggregation."}
        )


def validate_start_year_month_format(pattern, start_year_month):
    if not re.match(pattern, start_year_month):
        raise toolkit.ValidationError(
            {
                "message": (
                    "Invalid format for 'start_year_month'. "
                    "Expected format is YYYY-MM."
                )
            }
        )


def validate_start_year_month_not_before_default(
    START_YEAR_MONTH_DEFAULT, start_year_month
):
    if start_year_month < START_YEAR_MONTH_DEFAULT:
        raise toolkit.ValidationError(
            {
                "message": (
                    "The start date must be later " f"than {START_YEAR_MONTH_DEFAULT}."
                )
            }
        )


def validate_end_year_month_format(pattern, end_year_month):
    if not re.match(pattern, end_year_month):
        raise toolkit.ValidationError(
            {
                "message": (
                    "Invalid format for 'end_year_month'. "
                    "Expected format is YYYY-MM."
                )
            }
        )


def validate_end_year_month_not_in_future(today, end_year_month):
    if end_year_month >= today.strftime('%Y-%m'):
        raise toolkit.ValidationError(
            {"message": "The selected period cannot be in the future."}
        )


def validate_period_months_ago(today, period_months_ago):
    if period_months_ago != PERIOD_MONTHS_AGO_ALL and (
        int(period_months_ago) <= 0
        or (today - relativedelta(months=int(period_months_ago))).strftime("%Y-%m")
        < START_YEAR_MONTH_DEFAULT
    ):
        raise toolkit.ValidationError(
            {
                "message": (
                    "The selected period is beyond the allowable range. "
                    f"Only periods up to {START_YEAR_MONTH_DEFAULT} are allowed."
                )
            }
        )


def validate_enable_orgs_in_config(enable_orgs):
    if not enable_orgs:
        raise toolkit.ValidationError(
            {
                "message": (
                    "There are no organizations with "
                    "the download feature enabled. "
                    "Please contact the site administrator for assistance."
                )
            }
        )


def validate_organization_name_in_group(organization_name):
    if not organization_name:
        return

    group_name_list = get_group_service.get_group_names(organization_name)

    if not group_name_list:
        raise toolkit.ValidationError(
            {
                "message": (
                    "The specified organization does not exist or "
                    "may have been deleted. Please enter a valid organization name."
                )
            }
        )


def validate_organization_download_enabled(organization_name, enable_org):
    if organization_name not in enable_org:
        raise toolkit.ValidationError(
            {
                "message": (
                    "A organization with the download feature "
                    "disabled has been selected. "
                    "Please contact the site administrator for assistance."
                )
            }
        )


def validate_download_function(is_feedback_config):
    if not is_feedback_config and not FeedbackConfig().download.is_enable():
        raise toolkit.ValidationError(
            {
                "message": (
                    "Download function is off. "
                    "Please contact the site administrator for assistance."
                )
            }
        )


def validate_aggregation_metric(aggregation_metric, aggregation_metric_list):
    if aggregation_metric not in aggregation_metric_list:
        raise toolkit.ValidationError(
            {"message": "This is a non-existent aggregation metric."}
        )
