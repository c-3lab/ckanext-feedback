import logging
import re
from datetime import datetime

from ckan.common import _, config
from ckan.logic import side_effect_free
from ckan.plugins import toolkit

import ckanext.feedback.services.ranking.dataset as dataset_ranking_service

log = logging.getLogger(__name__)


@side_effect_free
def datasets_ranking(context, data_dict):
    top_ranked_limit = data_dict.get('top_ranked_limit', 5)
    period_months_ago = data_dict.get('period_months_ago')
    start_year_month = data_dict.get('start_year_month')
    end_year_month = data_dict.get('end_year_month')
    aggregation_metric = data_dict.get('aggregation_metric', 'download')
    municipality_name = data_dict.get('municipality_name')

    # top_ranked_limitが最低値（1）最大値（100）の間で入力されたか
    if not (1 <= int(top_ranked_limit) <= 100):
        raise toolkit.ValidationError(
            {
                "__type": "Range Error",
                "message": _("The 'top_ranked_limit' must be between 1 and 100."),
            }
        )

    # 集計期間が設定されているか
    if not period_months_ago and not start_year_month and not end_year_month:
        raise toolkit.ValidationError(
            {
                "__type": "Missing Parameter Error",
                "message": _("Please set the period for aggregation."),
            }
        )

    today = datetime.now()
    pattern = r"^\d{4}-(0[1-9]|1[0-2])$"

    if not period_months_ago:
        if start_year_month:
            # start_year_monthのフォーマットが正しいか
            if not re.match(pattern, start_year_month):
                msg = (
                    "Invalid format for 'start_year_month'. Expected format is YYYY-MM."
                )
                raise toolkit.ValidationError(
                    {
                        "__type": "Format Error",
                        "message": _(msg),
                    }
                )

            # start_year_monthのみ入力した場合
            if start_year_month and not end_year_month:
                if today.month == 1:
                    end_year_month = f'{today.year}-12'
                else:
                    end_year_month = f'{today.year}-{(today.month - 1):02d}'

        if end_year_month:
            # end_year_monthのフォーマットが正しいか
            if not re.match(pattern, end_year_month):
                msg = "Invalid format for 'end_year_month'. Expected format is YYYY-MM."
                raise toolkit.ValidationError(
                    {
                        "__type": "Range Error",
                        "message": _(msg),
                    }
                )

            # end_year_monthのみ入力した場合
            if not start_year_month and end_year_month:
                start_year_month = "1000-01"

    if period_months_ago:
        if period_months_ago == "all":
            start_year_month = "1000-01"
            if today.month == 1:
                end_year_month = f'{today.year}-12'
            else:
                end_year_month = f'{today.year}-{(today.month - 1):02d}'
        elif period_months_ago in [str(i) for i in range(1, 13)]:
            period_months_ago_int = int(period_months_ago)
            if (today.month - period_months_ago_int) >= 1:
                start_year_month = (
                    f'{today.year}-{(today.month - period_months_ago_int):02d}'
                )
            else:
                start_year_month = (
                    f'{today.year-1}-{((today.month+12)-period_months_ago_int):02d}'
                )

            if today.month == 1:
                end_year_month = f'{today.year}-12'
            else:
                end_year_month = f'{today.year}-{(today.month - 1):02d}'
        else:
            raise toolkit.ValidationError(
                {
                    "__type": "Range Error",
                    "message": _(
                        "The 'period_months_ago' must be between 1 and 12, or 'all'."
                    ),
                }
            )

    if aggregation_metric == 'download':
        enable_org = config.get('ckan.feedback.downloads.enable_orgs', [])

        if not enable_org:
            raise toolkit.ValidationError(
                {
                    "__type": "Validation Error",
                    "message": _(
                        "There are no municipalities with the download feature enabled."
                    ),
                }
            )

        msg = "A municipality with the download feature disabled has been selected."

        if municipality_name:
            if municipality_name not in enable_org:
                raise toolkit.ValidationError(
                    {
                        "__type": "Validation Error",
                        "message": _(msg),
                    }
                )
            enable_org = [municipality_name]

        results = dataset_ranking_service.get_download_ranking(
            enable_org,
            top_ranked_limit,
            period_months_ago,
            start_year_month,
            end_year_month,
        )
    elif aggregation_metric == 'like':
        raise toolkit.ValidationError(
            {"__type": "", "message": _("This is a non-existent aggregation metric.")}
        )
    elif aggregation_metric == 'comment':
        raise toolkit.ValidationError(
            {"__type": "", "message": _("This is a non-existent aggregation metric.")}
        )
    elif aggregation_metric == 'utilization':
        raise toolkit.ValidationError(
            {"__type": "", "message": _("This is a non-existent aggregation metric.")}
        )
    elif aggregation_metric == 'issue_resolution':
        raise toolkit.ValidationError(
            {"__type": "", "message": _("This is a non-existent aggregation metric.")}
        )
    else:
        raise toolkit.ValidationError(
            {"__type": "", "message": _("This is a non-existent aggregation metric.")}
        )

    dateset_ranking_list = []

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

        dateset_ranking_list.append(dataset_ranking_dict)

    return dateset_ranking_list
