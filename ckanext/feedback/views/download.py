import logging

import ckan.views.resource as resource
from flask import Blueprint

from ckanext.feedback.controllers.download import DownloadController
from ckanext.feedback.services.common.config import FeedbackConfig, download_handler
from ckanext.feedback.services.resource.comment import get_resource
from ckanext.feedback.views.error_handler import add_error_handler

log = logging.getLogger(__name__)

blueprint = Blueprint(
    'download',
    __name__,
    url_prefix='/dataset/<id>/resource',
    url_defaults={'package_type': 'dataset'},
)

# Add target page URLs to rules and add each URL to the blueprint
blueprint.add_url_rule(
    '/<resource_id>/download/<filename>', view_func=DownloadController.extended_download
)
blueprint.add_url_rule(
    '/<resource_id>/download',
    'download',
    view_func=DownloadController.extended_download,
)


@add_error_handler
def get_download_blueprint():
    return blueprint


# Handler to Use When Called from External Extensions
def download(package_type, id, resource_id, filename=None):
    if filename is None:
        filename = get_resource(resource_id).Resource.url

    if FeedbackConfig().download.is_enable():
        handler = DownloadController.extended_download
    else:
        handler = download_handler()
        if not handler:
            log.debug('Use default CKAN callback for resource.download')
            handler = resource.download
    return handler(
        package_type=package_type,
        id=id,
        resource_id=resource_id,
        filename=filename,
    )
