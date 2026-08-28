import ckan.model as model
from ckan.logic.action.get import package_show as core_package_show
from ckan.plugins import toolkit

from ckanext.feedback.utils.feedback_fields import add_package_feedback_fields
from ckanext.feedback.utils.legacy_fields import remove_legacy_package_feedback_fields


@toolkit.side_effect_free
def package_show(context, data_dict):
    package_dict = core_package_show(
        context,
        data_dict,
    )

    # Temporarily exclude legacy fields loaded from the database.
    remove_legacy_package_feedback_fields(package_dict)

    package = model.Package.get(package_dict["id"])

    if package is None:
        return package_dict

    add_package_feedback_fields([package_dict])

    return package_dict
