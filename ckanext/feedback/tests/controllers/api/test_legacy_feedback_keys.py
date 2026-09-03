from ckanext.feedback.controllers.api.package_show import remove_legacy_feedback_fields
from ckanext.feedback.controllers.api.resource_show import (
    remove_legacy_feedback_fields as remove_resource_legacy_feedback_fields,
)


def test_remove_legacy_feedback_fields_removes_japanese_keys_from_resources():
    package_dict = {
        "id": "test-package-id",
        "extras": [],
        "resources": [
            {
                "id": "test-resource-id",
                "いいね数": 123,
                "コメント数": 0,
                "feedback_like_count": 123,
            }
        ],
    }

    remove_legacy_feedback_fields(package_dict)

    resource_dict = package_dict["resources"][0]
    assert "いいね数" not in resource_dict
    assert "コメント数" not in resource_dict
    assert resource_dict["feedback_like_count"] == 123


def test_remove_resource_legacy_feedback_fields_removes_japanese_keys():
    resource_dict = {
        "id": "test-resource-id",
        "いいね数": 123,
        "コメント数": 0,
    }

    remove_resource_legacy_feedback_fields(resource_dict)

    assert "いいね数" not in resource_dict
    assert "コメント数" not in resource_dict
