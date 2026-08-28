"""Utilities for attaching feedback values to package dictionaries.

Feedback counts change without the dataset itself being modified, so the
values Solr holds are only a snapshot taken when the dataset was last
indexed. They are therefore read from the database and written over whatever
the caller already has.
"""

from ckanext.feedback.services.common.config import FeedbackConfig
from ckanext.feedback.services.package import summary as package_summary_service
from ckanext.feedback.services.package.summary import get_package_id_from_packages

# stats key -> extras key on the package
PACKAGE_FEEDBACK_KEYS = {
    "like_count": "feedback_total_like_count",
    "comments": "feedback_total_comments",
    "downloads": "feedback_total_downloads",
    "utilizations": "feedback_total_utilizations",
    "issue_resolutions": "feedback_total_issue_resolutions",
    "rating": "feedback_average_rating",
}

# stats key -> field name on the resource
RESOURCE_FEEDBACK_KEYS = {
    "like_count": "feedback_like_count",
    "comments": "feedback_comments",
    "downloads": "feedback_downloads",
    "utilizations": "feedback_utilizations",
    "issue_resolutions": "feedback_issue_resolutions",
    "rating": "feedback_rating",
}


def _enabled_stats(cfg, owner_org):
    """Return the stats keys enabled for the organization"""

    enabled = set()

    if cfg.download.is_enable(owner_org):
        enabled.add("downloads")

    if cfg.utilization.is_enable(owner_org):
        enabled.update(("utilizations", "issue_resolutions"))

    if cfg.resource_comment.is_enable(owner_org):
        enabled.add("comments")
        if cfg.resource_comment.rating.is_enable(owner_org):
            enabled.add("rating")

    if cfg.like.is_enable(owner_org):
        enabled.add("like_count")

    return enabled


def add_package_feedback_fields(package_dicts, cfg=None):
    """Set the current feedback values on packages and their resources"""

    if not package_dicts:
        return

    cfg = cfg or FeedbackConfig()

    package_stats = package_summary_service.get_package_feedback_stats_bulk(
        package_dicts
    )
    resource_stats = package_summary_service.get_resource_feedback_stats_bulk(
        [
            resource_dict["id"]
            for package_dict in package_dicts
            for resource_dict in package_dict.get("resources", [])
            if resource_dict.get("id")
        ]
    )

    for package_dict in package_dicts:
        package_id = get_package_id_from_packages(package_dict)

        if package_id is None:
            continue

        enabled = _enabled_stats(cfg, package_dict.get("owner_org"))
        stats = package_stats.get(package_id, {})

        extras = [
            extra
            for extra in package_dict.get("extras") or []
            if extra.get("key") not in PACKAGE_FEEDBACK_KEYS.values()
        ]
        extras.extend(
            {"key": key, "value": stats.get(stats_key, 0)}
            for stats_key, key in PACKAGE_FEEDBACK_KEYS.items()
            if stats_key in enabled
        )
        package_dict["extras"] = extras

        for resource_dict in package_dict.get("resources", []):
            stats = resource_stats.get(resource_dict.get("id"), {})

            for stats_key, key in RESOURCE_FEEDBACK_KEYS.items():
                if stats_key in enabled:
                    resource_dict[key] = stats.get(stats_key, 0)
                else:
                    resource_dict.pop(key, None)
