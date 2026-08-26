import ckan.model as model
from ckan.logic import get_action

from ckanext.feedback.services.package import summary as package_summary_service


def package_show(context, data_dict):

    package_dict = get_action('package_show')(
        dict(context, ignore_auth=True, feedback_original=True),
        data_dict,
    )

    package = model.Package.get(package_dict['id'])

    if package is None:
        return package_dict

    extras = package_dict.setdefault('extras', [])

    stats_by_id = package_summary_service.get_package_feedback_stats_bulk(
        [package_dict]
    )

    stats = stats_by_id.get(package_dict['id'], {})

    extras.extend(
        [
            {
                'key': 'feedback_total_like_count',
                'value': stats.get('like_count', 0),
            },
            {
                'key': 'feedback_total_comments',
                'value': stats.get('comments', 0),
            },
            {
                'key': 'feedback_total_downloads',
                'value': stats.get('downloads', 0),
            },
            {
                'key': 'feedback_total_utilizations',
                'value': stats.get('utilizations', 0),
            },
            {
                'key': 'feedback_total_issue_resolutions',
                'value': stats.get('issue_resolutions', 0),
            },
            {
                'key': 'feedback_average_rating',
                'value': stats.get('rating', 0),
            },
        ]
    )

    return package_dict
