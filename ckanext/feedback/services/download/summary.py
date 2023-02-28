import uuid
import logging
import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError
from ckan.model import Resource
from ckanext.feedback.models.download import DownloadSummary
from psycopg2.errors import UndefinedTable

session = Session()
log = logging.getLogger(__name__)


def get_package_downloads(package_id):
    try:
        count = (
            session.query(func.sum(DownloadSummary.download))
            .join(Resource)
            .filter(Resource.package_id == package_id)
            .scalar()
        )
        return count or 0
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            log.error(
                'download_summary table does not exit.'
                ' Run "ckan --config=/etc/ckan/production.ini feedback init".'
            )
        raise
    finally:
        session.rollback()


def get_resource_downloads(resource_id):
    try:
        count = (
            session.query(DownloadSummary.download)
            .filter(DownloadSummary.resource_id == resource_id)
            .scalar()
        )
        return count or 0
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            log.error(
                'download_summary table does not exit.'
                ' Run "ckan --config=/etc/ckan/production.ini feedback init".'
            )
        raise
    finally:
        session.rollback()


def increment_resource_downloads(resource_id):
    try:
        download_summary = (
            session.query(DownloadSummary)
            .filter(DownloadSummary.resource_id == resource_id)
            .first()
        )
        if download_summary is None:
            download_summary = DownloadSummary(
                str(uuid.uuid4()),
                resource_id,
                1,
                datetime.datetime.now(),
                datetime.datetime.now(),
            )
            session.add(download_summary)
        else:
            download_summary.download = download_summary.download + 1
            download_summary.updated = datetime.datetime.now()
        session.commit()
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            log.error(
                'download_summary table does not exit.'
                ' Run "ckan --config=/etc/ckan/production.ini feedback init".'
            )
        raise
    finally:
        session.rollback()
