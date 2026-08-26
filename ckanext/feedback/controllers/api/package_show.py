import ckan.model as model
from ckan.logic.action.get import package_show as core_package_show
from ckan.plugins import toolkit

from ckanext.feedback.services.package import summary as package_summary_service


@toolkit.side_effect_free
def package_show(context, data_dict):

    package_dict = core_package_show(
        context,
        data_dict,
    )

    package = model.Package.get(package_dict["id"])

    if package is None:
        return package_dict

    stats_by_id = package_summary_service.get_package_feedback_stats_bulk(
        [package_dict]
    )

    stats = stats_by_id.get(package_dict["id"], {})

    extras = package_dict.setdefault("extras", [])

    existing_keys = {extra.get("key") for extra in extras}

    mappings = {
        "feedback_total_like_count": stats.get("like_count", 0),
        "feedback_total_comments": stats.get("comments", 0),
        "feedback_total_downloads": stats.get("downloads", 0),
        "feedback_total_utilizations": stats.get("utilizations", 0),
        "feedback_total_issue_resolutions": stats.get("issue_resolutions", 0),
        "feedback_average_rating": stats.get("rating", 0),
    }

    for key, value in mappings.items():

        if key in existing_keys:
            continue

        extras.append(
            {
                "key": key,
                "value": value,
            }
        )

    return package_dict
