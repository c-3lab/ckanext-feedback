from unittest.mock import patch

from ckanext.feedback.controllers.api.resource_show import resource_show


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


@patch(
    "ckanext.feedback.controllers.api.resource_show.resource_summary_service"
    ".get_resource_feedback_stats"
)
@patch("ckanext.feedback.controllers.api.resource_show.model.Resource.get")
@patch("ckanext.feedback.controllers.api.resource_show.core_resource_show")
def test_resource_show_removes_legacy_keys_and_sets_feedback_fields(
    mock_core_resource_show,
    mock_resource_get,
    mock_get_resource_feedback_stats,
):
    resource_dict = {
        "id": "test-resource-id",
        "いいね数": 999,
        "コメント数": 0,
    }

    mock_core_resource_show.return_value = resource_dict
    mock_resource_get.return_value = object()
    mock_get_resource_feedback_stats.return_value = {
        "like_count": 123,
        "downloads": 117,
        "utilizations": 0,
        "comments": 0,
        "issue_resolutions": 0,
        "rating": 0,
    }

    result = resource_show({}, {})

    assert "いいね数" not in result
    assert "コメント数" not in result
    assert result["feedback_like_count"] == 123
    assert result["feedback_downloads"] == 117
