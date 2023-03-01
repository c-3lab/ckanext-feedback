from flask import Blueprint

from ckanext.feedback.controllers.download import DownloadController
from ckanext.feedback.views.error_handler import add_error_handler

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
    '/<resource_id>/download', view_func=DownloadController.extended_download
)


@add_error_handler
def get_download_blueprint():
    return blueprint
