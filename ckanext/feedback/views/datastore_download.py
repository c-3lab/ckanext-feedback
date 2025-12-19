import logging
import re

from flask import Blueprint, request
from psycopg2.errors import UndefinedTable
from sqlalchemy.exc import ProgrammingError

from ckanext.feedback.models.session import session
from ckanext.feedback.services.download.monthly import (
    increment_resource_downloads_monthly,
)
from ckanext.feedback.services.download.summary import increment_resource_downloads

log = logging.getLogger(__name__)

# Blueprint for intercepting DataStore downloads
# Note: We don't use @route decorators because the datastore plugin
# registers /datastore/dump/<resource_id> first. Instead, we use
# before_app_request to intercept ALL requests and check if they
# match the DataStore download pattern.
datastore_blueprint = Blueprint(
    'feedback_datastore_override',
    __name__,
    url_prefix='',
)


# Error handlers must be registered before the blueprint is registered with the app
@datastore_blueprint.errorhandler(ProgrammingError)
def handle_programming_error(e):
    if isinstance(e.orig, UndefinedTable):
        log.error(
            'Some tables does not exit.'
            ' Run "ckan --config=/etc/ckan/production.ini feedback init".'
        )
    session.rollback()
    raise e


@datastore_blueprint.errorhandler(Exception)
def handle_exception(e):
    session.rollback()
    raise e


@datastore_blueprint.before_app_request
def intercept_datastore_download():
    "Intercept DataStore downloads and increment counters."

    # Early return for non-datastore paths (performance optimization)
    if not request.path.startswith('/datastore/dump/'):
        return None

    # Match DataStore download URLs: /datastore/dump/<resource_id>
    # UUID pattern: 8-4-4-4-12 hex characters with dashes
    # Note: request.path does not include query parameters
    UUID_PATTERN = (
        r'^/datastore/dump/'
        r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
        r'/?$'
    )
    match = re.match(UUID_PATTERN, request.path, re.IGNORECASE)

    if match and request.method == 'GET':
        resource_id = match.group(1)

        try:
            # Increment download counters
            increment_resource_downloads(resource_id)
            increment_resource_downloads_monthly(resource_id)
            session.commit()
        except Exception as e:
            session.rollback()
            log.warning(f'Transaction rolled back for resource {resource_id}')
            log.warning(f'Failed to increment download count for {resource_id}: {e}')

    return None


def get_datastore_download_blueprint():
    return datastore_blueprint
