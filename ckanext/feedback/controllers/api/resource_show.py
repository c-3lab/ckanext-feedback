import ckan.model as model
from ckan.logic.action.get import resource_show as core_resource_show
from ckan.plugins import toolkit

from ckanext.feedback.lib import helpers as feedback_helpers


def remove_legacy_feedback_fields(resource_dict):
    """Exclude legacy feedback items from the API response."""

    feedback_helpers.strip_resource_feedback_fields(resource_dict)


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

    feedback_helpers.populate_resource_feedback_fields(resource_dict)

    return resource_dict
