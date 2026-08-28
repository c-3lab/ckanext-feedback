from ckan.logic.action.get import resource_show as core_resource_show
from ckan.plugins import toolkit

from ckanext.feedback.utils.legacy_fields import remove_legacy_resource_feedback_fields


@toolkit.side_effect_free
def resource_show(context, data_dict):
    resource_dict = core_resource_show(
        context,
        data_dict,
    )

    remove_legacy_resource_feedback_fields(resource_dict)

    return resource_dict
