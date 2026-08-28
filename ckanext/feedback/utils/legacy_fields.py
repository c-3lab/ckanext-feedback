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
    """Exclude legacy feedback items from the resource dictionary"""

    for key in LEGACY_FEEDBACK_KEYS:
        resource_dict.pop(key, None)


def remove_legacy_package_feedback_fields(package_dict):
    """Exclude old feedback items from the dictionary"""

    package_dict["extras"] = [
        extra
        for extra in package_dict.get("extras", [])
        if extra.get("key") not in LEGACY_FEEDBACK_KEYS
    ]

    for resource_dict in package_dict.get("resources", []):
        remove_legacy_resource_feedback_fields(resource_dict)
