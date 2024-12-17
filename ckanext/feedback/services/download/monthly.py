import logging
import uuid
from datetime import datetime

from sqlalchemy import extract

from ckanext.feedback.models.download import DownloadMonthly
from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


def increment_resource_downloads_monthly(resource_id):
    current_year = datetime.now().year
    current_month = datetime.now().month

    download_monthly = (
        session.query(DownloadMonthly)
        .filter(
            DownloadMonthly.resource_id == resource_id,
            extract('year', DownloadMonthly.created) == current_year,
            extract('month', DownloadMonthly.created) == current_month,
        )
        .first()
    )
    if download_monthly is None:
        download_monthly = DownloadMonthly(
            id=str(uuid.uuid4()),
            resource_id=resource_id,
            download_count=1,
            created=datetime.now(),
            updated=datetime.now(),
        )
        session.add(download_monthly)
    else:
        download_monthly.download_count = download_monthly.download_count + 1
        download_monthly.updated = datetime.now()
    session.commit()
