import logging

from flask import Blueprint, request

from ckanext.datastore.blueprint import dump as original_dump
from ckanext.feedback.services.download.monthly import (
    increment_resource_downloads_monthly,
)
from ckanext.feedback.services.download.summary import increment_resource_downloads

log = logging.getLogger(__name__)

# Blueprint for overriding DataStore functionality
datastore_blueprint = Blueprint(
    'feedback_datastore_override',
    __name__,
    url_prefix='',
)


@datastore_blueprint.route('/datastore/dump/<resource_id>')
@datastore_blueprint.route('/datastore/dump/<resource_id>/')
@datastore_blueprint.before_app_request
def datastore_dump(resource_id=None):
    """Intercept DataStore downloads"""

    # Check if this is a DataStore download request
    if '/datastore/dump/' not in request.path:
        return

    # Extract resource_id from URL if not provided
    if not resource_id:
        import re

        match = re.search(r'/datastore/dump/([^/?]+)', request.path)
        resource_id = match.group(1) if match else None

    # Increment download count
    if resource_id:
        increment_resource_downloads(resource_id)
        increment_resource_downloads_monthly(resource_id)

    # Call original DataStore dump function
    response = original_dump(resource_id)
    return response


def get_datastore_download_blueprint():
    return datastore_blueprint
