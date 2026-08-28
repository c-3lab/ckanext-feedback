from ckan.logic.action.get import resource_search as core_resource_search
from ckan.plugins import toolkit

from ckanext.feedback.utils.legacy_fields import remove_legacy_resource_feedback_fields


@toolkit.side_effect_free
def resource_search(context, data_dict):
    result = core_resource_search(
        context,
        data_dict,
    )

    for resource_dict in result.get("results", []):
        remove_legacy_resource_feedback_fields(resource_dict)

    return result
