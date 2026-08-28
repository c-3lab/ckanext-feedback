"""Temporary compatibility utilities for legacy feedback fields.

Remove these helpers after the legacy database migration is complete.
"""

LEGACY_FEEDBACK_KEYS = {
    "いいね数",
    "コメント数",
    "ダウンロード数",
    "利活用数",
    "課題解決数",
    "評価",
    "Number of Likes",
    "Comments",
    "Downloads",
    "Utilizations",
    "Issue Resolutions",
    "Rating",
}


def remove_legacy_resource_feedback_fields(resource_dict):
    """Remove legacy feedback fields from a resource dictionary"""

    for key in LEGACY_FEEDBACK_KEYS:
        resource_dict.pop(key, None)


def remove_legacy_package_feedback_fields(package_dict):
    """Remove legacy feedback fields from a package dictionary"""

    package_dict["extras"] = [
        extra
        for extra in package_dict.get("extras", [])
        if extra.get("key") not in LEGACY_FEEDBACK_KEYS
    ]

    for resource_dict in package_dict.get("resources", []):
        remove_legacy_resource_feedback_fields(resource_dict)
