from unittest.mock import patch

from ckan.common import config

from ckanext.feedback.controllers.api.resource_show import resource_show
from ckanext.feedback.services.common.config import FeedbackConfig


@patch("ckanext.feedback.controllers.api.resource_show.model.Resource.get")
@patch("ckanext.feedback.controllers.api.resource_show.core_resource_show")
def test_resource_show_resource_not_found(
    mock_core_resource_show,
    mock_resource_get,
):
    resource_dict = {
        "id": "test-resource-id",
    }

    mock_core_resource_show.return_value = resource_dict
    mock_resource_get.return_value = None

    result = resource_show({}, {})

    assert result == resource_dict


@patch("ckanext.feedback.lib.helpers.model.Package.get")
@patch(
    "ckanext.feedback.lib.helpers.resource_summary_service"
    ".get_resource_feedback_stats"
)
@patch("ckanext.feedback.controllers.api.resource_show.model.Resource.get")
@patch("ckanext.feedback.controllers.api.resource_show.core_resource_show")
def test_resource_show_removes_legacy_keys_and_sets_feedback_fields(
    mock_core_resource_show,
    mock_resource_get,
    mock_get_resource_feedback_stats,
    mock_package_get,
):
    resource_dict = {
        "id": "test-resource-id",
        "package_id": "test-package-id",
        "いいね数": 999,
        "コメント数": 0,
    }

    mock_core_resource_show.return_value = resource_dict
    mock_resource_get.return_value = object()
    mock_package_get.return_value = type(
        'Package', (), {'owner_org': None}
    )()
    mock_get_resource_feedback_stats.return_value = {
        "like_count": 123,
        "downloads": 117,
        "utilizations": 0,
        "comments": 0,
        "issue_resolutions": 0,
        "rating": 0,
    }

    config[f"{FeedbackConfig().like.get_ckan_conf_str()}.enable"] = True
    config[f"{FeedbackConfig().download.get_ckan_conf_str()}.enable"] = True
    config[f"{FeedbackConfig().utilization.get_ckan_conf_str()}.enable"] = True
    config[f"{FeedbackConfig().resource_comment.get_ckan_conf_str()}.enable"] = True

    result = resource_show({}, {})

    assert "いいね数" not in result
    assert "コメント数" not in result
    assert result["feedback_like_count"] == 123
    assert result["feedback_downloads"] == 117
