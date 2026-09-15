import ckan.model as model
from ckan.logic.action.get import package_show as core_package_show
from ckan.plugins import toolkit

from ckanext.feedback.lib import helpers as feedback_helpers
from ckanext.feedback.services.package import summary as package_summary_service

# Re-export for backwards compatibility with existing imports/tests.
LEGACY_FEEDBACK_KEYS = feedback_helpers.LEGACY_FEEDBACK_KEYS


def remove_legacy_feedback_fields(package_dict):
    """Exclude legacy feedback items from the API response."""

    # Exclude old keys from the dataset's extras
    package_dict["extras"] = [
        extra
        for extra in package_dict.get("extras", [])
        if extra.get("key") not in LEGACY_FEEDBACK_KEYS
        and extra.get("key") not in feedback_helpers.PACKAGE_FEEDBACK_EXTRA_KEYS
    ]

    # Exclude feedback keys from the root of each resource
    for resource_dict in package_dict.get("resources", []):
        feedback_helpers.strip_resource_feedback_fields(resource_dict)


@toolkit.side_effect_free
def package_show(context, data_dict):

    package_dict = core_package_show(
        context,
        data_dict,
    )

    # Exclude legacy fields returned by core_package_show
    remove_legacy_feedback_fields(package_dict)

    package = model.Package.get(package_dict["id"])

    if package is None:
        return package_dict

    stats_by_id = package_summary_service.get_package_feedback_stats_bulk(
        [package_dict]
    )

    stats = stats_by_id.get(package_dict["id"], {})

    feedback_helpers.populate_package_feedback_extras(package_dict, stats)

    for resource_dict in package_dict.get("resources", []):
        feedback_helpers.populate_resource_feedback_fields(resource_dict)

    return package_dict
