import ckan.model as model
from ckan.logic.action.get import resource_show as core_resource_show
from ckan.plugins import toolkit

from ckanext.feedback.controllers.api.package_show import LEGACY_FEEDBACK_KEYS
from ckanext.feedback.services.resource import summary as resource_summary_service


def remove_legacy_feedback_fields(resource_dict):
    """Exclude legacy feedback items from the API response."""

    for key in LEGACY_FEEDBACK_KEYS:
        resource_dict.pop(key, None)


@toolkit.side_effect_free
def resource_show(context, data_dict):

    resource_dict = core_resource_show(
        context,
        data_dict,
    )

    # Exclude legacy fields returned by core_resource_show
    remove_legacy_feedback_fields(resource_dict)

    resource = model.Resource.get(resource_dict["id"])

    if resource is None:
        return resource_dict

    stats = resource_summary_service.get_resource_feedback_stats(resource_dict["id"])

    mappings = {
        "feedback_like_count": stats.get("like_count", 0),
        "feedback_downloads": stats.get("downloads", 0),
        "feedback_utilizations": stats.get("utilizations", 0),
        "feedback_comments": stats.get("comments", 0),
        "feedback_issue_resolutions": stats.get("issue_resolutions", 0),
        "feedback_rating": stats.get("rating", 0),
    }

    for key, value in mappings.items():
        resource_dict[key] = value

    return resource_dict
