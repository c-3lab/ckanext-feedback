import logging
import re
from datetime import datetime
from pathlib import Path

from ckan.common import config
from ckan.logic import side_effect_free
from ckan.plugins import toolkit
from dateutil.relativedelta import relativedelta

import ckanext.feedback.services.ranking.dataset as dataset_ranking_service
from ckanext.feedback.services.common.config import FeedbackConfig

log = logging.getLogger(__name__)


# Default constants
TOP_RANKED_LIMIT_DEFAULT = 5
PERIOD_MONTHS_AGO_ALL = 'all'
START_YEAR_MONTH_DEFAULT = '2006-10'
AGGREGATION_METRIC_DOWNLOAD = 'download'


@side_effect_free
def datasets_ranking(context, data_dict):
    """
    Fetch and return a ranking of datasets based on download counts
    or other aggregation metrics for a given period and conditions.
    """
    # Retrieve input values or use defaults
    top_ranked_limit = data_dict.get('top_ranked_limit', TOP_RANKED_LIMIT_DEFAULT)
    period_months_ago = data_dict.get('period_months_ago')
    start_year_month_input = data_dict.get('start_year_month')
    end_year_month_input = data_dict.get('end_year_month')
    aggregation_metric = data_dict.get(
        'aggregation_metric', AGGREGATION_METRIC_DOWNLOAD
    )
    municipality_name = data_dict.get('municipality_name')

    # # Ensure 'top_ranked_limit' is between 1 and 100
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

    # Load feedback configuration file path
    feedback_config_path = config.get('ckan.feedback.config_file', '/srv/app')
    file_path = Path(f'{feedback_config_path}/feedback_config.json')

    # Check if feedback configuration file exists
    is_feedback_config = file_path.is_file()

    enable_orgs = []
    dataset_ranking_list = []

    if aggregation_metric == AGGREGATION_METRIC_DOWNLOAD:
        # Get dataset download ranking data
        results = get_dataset_download_ranking(
            is_feedback_config,
            enable_orgs,
            top_ranked_limit,
            start_year_month,
            end_year_month,
            municipality_name,
        )

        # Format and append results to the ranking list
        dataset_ranking_list = generate_dataset_ranking_list(
            dataset_ranking_list, results
        )

    return dataset_ranking_list


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
        validate_start_year_month(pattern, start_year_month)

    if end_year_month:
        # Validate the format of end_year_month
        validate_end_year_month(pattern, end_year_month)

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
    validate_period_months_ago(period_months_ago)

    # Default start year-month
    tmp_start_year_month = START_YEAR_MONTH_DEFAULT

    # Calculate start year-month based on period if numeric
    if period_months_ago in [str(i) for i in range(1, 13)]:
        period_months_ago_int = int(period_months_ago)

        tmp_start_year_month = (
            today - relativedelta(months=period_months_ago_int)
        ).strftime("%Y-%m")

    start_year_month = tmp_start_year_month
    # End year-month is always set to the last month
    end_year_month = (today - relativedelta(months=1)).strftime("%Y-%m")

    return start_year_month, end_year_month


def get_dataset_download_ranking(
    is_feedback_config,
    enable_orgs,
    top_ranked_limit,
    start_year_month,
    end_year_month,
    municipality_name,
):
    """
    Retrieve dataset download ranking data based on input parameters.
    """
    # Raise an error if download functionality is off and feedback config is missing
    validate_download_function(is_feedback_config)

    if is_feedback_config:
        # Load the list of municipalities with download feature enabled
        enable_orgs = config.get('ckan.feedback.downloads.enable_orgs', [])

        # Validate the existence of enabled organizations
        validate_enable_orgs(enable_orgs)

        if municipality_name:
            # Ensure the municipality has downloads enabled
            validate_municipality_name(municipality_name, enable_orgs)
            enable_orgs = [municipality_name]

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


def validate_start_year_month(pattern, start_year_month):
    if not re.match(pattern, start_year_month):
        raise toolkit.ValidationError(
            {
                "message": "Invalid format for 'start_year_month'. "
                "Expected format is YYYY-MM."
            }
        )


def validate_end_year_month(pattern, end_year_month):
    if not re.match(pattern, end_year_month):
        raise toolkit.ValidationError(
            {
                "message": "Invalid format for 'end_year_month'. "
                "Expected format is YYYY-MM."
            }
        )


def validate_period_months_ago(period_months_ago):
    if period_months_ago not in [PERIOD_MONTHS_AGO_ALL] + [
        str(i) for i in range(1, 13)
    ]:
        raise toolkit.ValidationError(
            {"message": "The 'period_months_ago' must be between 1 and 12, or 'all'."}
        )


def validate_enable_orgs(enable_orgs):
    if not enable_orgs:
        raise toolkit.ValidationError(
            {
                "message": "There are no municipalities with "
                "the download feature enabled."
            }
        )


def validate_municipality_name(municipality_name, enable_org):
    if municipality_name not in enable_org:
        raise toolkit.ValidationError(
            {
                "message": "A municipality with the download feature disabled "
                "has been selected."
            }
        )


def validate_download_function(is_feedback_config):
    if not is_feedback_config and not FeedbackConfig().download.is_enable:
        raise toolkit.ValidationError({"message": "Download function is off."})


def validate_aggregation_metric(aggregation_metric, aggregation_metric_list):
    if aggregation_metric not in aggregation_metric_list:
        raise toolkit.ValidationError(
            {"message": "This is a non-existent aggregation metric."}
        )
