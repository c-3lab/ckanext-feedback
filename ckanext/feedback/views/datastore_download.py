import logging

from flask import Blueprint

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
def datastore_dump(resource_id):
    """Intercept DataStore downloads"""

    increment_resource_downloads(resource_id)
    increment_resource_downloads_monthly(resource_id)

    return original_dump(resource_id)


def get_datastore_download_blueprint():
    return datastore_blueprint
