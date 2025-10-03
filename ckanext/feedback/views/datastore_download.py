import logging
import re

from flask import Blueprint, request

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


@datastore_blueprint.before_app_request
def intercept_datastore_download():
    """Intercept DataStore downloads and increment counters.

    This function runs BEFORE Flask's routing, allowing us to track
    downloads even when the datastore plugin's route is matched first.

    How it works:
    1. Checks if the request path matches /datastore/dump/<resource_id>
    2. If yes, increments the download counters
    3. Returns None to let Flask continue normal routing to datastore plugin
    """
    # Match DataStore download URLs: /datastore/dump/<resource_id>
    match = re.match(r'^/datastore/dump/([^/?]+)', request.path)

    if match and request.method == 'GET':
        resource_id = match.group(1)

        try:
            # Increment download counters
            increment_resource_downloads(resource_id)
            increment_resource_downloads_monthly(resource_id)
            log.info(f"Download count incremented for resource: {resource_id}")
        except Exception as e:
            # Don't fail the request if counting fails
            log.warning(f"Failed to increment download count for {resource_id}: {e}")

    # Return None to continue normal request handling
    # Flask will route the request to datastore plugin's dump function
    return None


def get_datastore_download_blueprint():
    return datastore_blueprint
