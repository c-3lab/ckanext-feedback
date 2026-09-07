from unittest.mock import patch

from ckan.common import config

from ckanext.feedback.controllers.api.package_show import package_show
from ckanext.feedback.services.common.config import FeedbackConfig


@patch("ckanext.feedback.controllers.api.package_show.model.Package.get")
@patch("ckanext.feedback.controllers.api.package_show.core_package_show")
def test_package_show_package_not_found(
    mock_core_package_show,
    mock_package_get,
):
    package_dict = {
        "id": "test-package-id",
        "extras": [],
    }

    mock_core_package_show.return_value = package_dict
    mock_package_get.return_value = None

    result = package_show({}, {})

    assert result == package_dict


@patch(
    "ckanext.feedback.controllers.api.package_show.package_summary_service"
    ".get_package_feedback_stats_bulk"
)
@patch("ckanext.feedback.lib.helpers.model.Package.get")
@patch("ckanext.feedback.controllers.api.package_show.model.Package.get")
@patch("ckanext.feedback.controllers.api.package_show.core_package_show")
def test_package_show_omits_feedback_fields_when_modules_disabled(
    mock_core_package_show,
    mock_package_get,
    mock_helpers_package_get,
    mock_get_package_feedback_stats_bulk,
):
    package_dict = {
        "id": "test-package-id",
        "owner_org": "test-org-id",
        "extras": [
            {
                "key": "feedback_total_like_count",
                "value": 99,
            }
        ],
        "resources": [
            {
                "id": "test-resource-id",
                "package_id": "test-package-id",
                "feedback_like_count": 99,
                "feedback_downloads": 99,
            }
        ],
    }

    mock_core_package_show.return_value = package_dict
    mock_package_get.return_value = object()
    mock_helpers_package_get.return_value = type(
        'Package', (), {'owner_org': 'test-org-id'}
    )()
    mock_get_package_feedback_stats_bulk.return_value = {
        "test-package-id": {
            "like_count": 5,
            "comments": 4,
            "downloads": 3,
            "utilizations": 2,
            "issue_resolutions": 1,
            "rating": 4.5,
        }
    }

    config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = False
    config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = False
    config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = False
    config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = False

    result = package_show({}, {"id": "test-package-id"})

    assert result["extras"] == []
    resource_dict = result["resources"][0]
    assert "feedback_like_count" not in resource_dict
    assert "feedback_downloads" not in resource_dict
