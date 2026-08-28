from ckan.logic.action.get import package_search as core_package_search
from ckan.plugins import toolkit

from ckanext.feedback.utils.legacy_fields import remove_legacy_package_feedback_fields


@toolkit.side_effect_free
def package_search(context, data_dict):
    search_result = core_package_search(
        context,
        data_dict,
    )

    for package_dict in search_result.get("results", []):
        remove_legacy_package_feedback_fields(package_dict)

    return search_result
