import logging
import re

from flask import Blueprint, request

from ckanext.feedback.services.download.monthly import (
    increment_resource_downloads_monthly,
)
from ckanext.feedback.services.download.summary import increment_resource_downloads
from ckanext.feedback.views.error_handler import add_error_handler

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


@datastore_blueprint.before_app_request
def intercept_datastore_download():
    "Intercept DataStore downloads and increment counters."

    # Match DataStore download URLs: /datastore/dump/<resource_id>
    match = re.match(r'^/datastore/dump/([^/?]+)', request.path)

    if match and request.method == 'GET':
        resource_id = match.group(1)

        try:
            # Increment download counters
            increment_resource_downloads(resource_id)
            increment_resource_downloads_monthly(resource_id)
            log.debug(f"Download count incremented for resource: {resource_id}")
        except Exception as e:
            # Don't fail the request if counting fails
            log.warning(f"Failed to increment download count for {resource_id}: {e}")

    return None


@add_error_handler
def get_datastore_download_blueprint():
    return datastore_blueprint
