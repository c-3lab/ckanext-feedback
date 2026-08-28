import logging

from ckanext.feedback.services.download import summary as download_summary_service
from ckanext.feedback.services.resource import likes as resource_likes_service
from ckanext.feedback.services.resource import summary as resource_summary_service
from ckanext.feedback.services.utilization import summary as utilization_summary_service

log = logging.getLogger(__name__)


def get_package_id_from_packages(package):
    if not package:
        return None
    pid = (
        package.get("id") if isinstance(package, dict) else getattr(package, "id", None)
    )
    if pid is None:
        return None
    s = str(pid).strip()
    return s if s and s != "None" else None


def get_package_feedback_stats_bulk(packages):
    if not packages:
        return {}

    package_ids = []
    for p in packages:
        if not p:
            continue

        pid = get_package_id_from_packages(p)
        if pid:
            package_ids.append(pid)
    if not package_ids:
        return {}

    likes = resource_likes_service.get_package_like_count_bulk(package_ids)
    downloads = download_summary_service.get_package_downloads_bulk(package_ids)
    utilizations = utilization_summary_service.get_package_utilizations_bulk(
        package_ids
    )
    comments = resource_summary_service.get_package_comments_bulk(package_ids)
    rating = resource_summary_service.get_package_rating_bulk(package_ids)
    issue_resolutions = utilization_summary_service.get_package_issue_resolutions_bulk(
        package_ids
    )

    by_id = {}

    for pid in package_ids:
        raw_rating = rating.get(pid, 0)
        by_id[pid] = {
            "like_count": likes.get(pid, 0),
            "downloads": downloads.get(pid, 0),
            "utilizations": utilizations.get(pid, 0),
            "comments": comments.get(pid, 0),
            "rating": 0 if raw_rating == 0 else round(raw_rating, 1),
            "issue_resolutions": issue_resolutions.get(pid, 0),
        }

    return by_id


def get_resource_feedback_stats_bulk(resource_ids):
    if not resource_ids:
        return {}

    likes = resource_likes_service.get_resource_like_count_bulk(resource_ids)
    downloads = download_summary_service.get_resource_downloads_bulk(resource_ids)
    utilizations = utilization_summary_service.get_resource_utilizations_bulk(
        resource_ids
    )
    comments = resource_summary_service.get_resource_comments_bulk(resource_ids)
    rating = resource_summary_service.get_resource_rating_bulk(resource_ids)
    issue_resolutions = utilization_summary_service.get_resource_issue_resolutions_bulk(
        resource_ids
    )

    return {
        rid: {
            "like_count": likes.get(rid, 0),
            "downloads": downloads.get(rid, 0),
            "utilizations": utilizations.get(rid, 0),
            "comments": comments.get(rid, 0),
            "rating": rating.get(rid, 0),
            "issue_resolutions": issue_resolutions.get(rid, 0),
        }
        for rid in resource_ids
    }
