import logging
import uuid
from datetime import datetime

from ckan.model import Resource
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


def get_package_downloads(package_id):
    count = (
        session.query(func.sum(DownloadSummary.download))
        .join(Resource)
        .filter(
            Resource.package_id == package_id,
            Resource.state == "active",
        )
        .scalar()
    )
    return count or 0


def get_resource_downloads(resource_id):
    count = (
        session.query(DownloadSummary.download)
        .filter(DownloadSummary.resource_id == resource_id)
        .scalar()
    )
    return count or 0


def increment_resource_downloads(resource_id):
    now = datetime.now()

    insert_download_summary = insert(DownloadSummary).values(
        id=str(uuid.uuid4()),
        resource_id=resource_id,
        download=1,
        created=now,
    )
    download_summary = insert_download_summary.on_conflict_do_update(
        index_elements=['resource_id'],
        set_={
            'download': DownloadSummary.download + 1,
            'updated': now,
        },
    )
    session.execute(download_summary)
