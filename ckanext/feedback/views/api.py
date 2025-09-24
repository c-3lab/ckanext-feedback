from flask import Blueprint

from ckanext.feedback.controllers.api import (
    moral_check_log as api_moral_check_log_controllers,
)
from ckanext.feedback.views.error_handler import add_error_handler

blueprint = Blueprint(
    'feedback_api',
    __name__,
    url_prefix='/api/feedback',
)

blueprint.add_url_rule(
    '/download_moral_check_log',
    'download_moral_check_log',
    view_func=api_moral_check_log_controllers.download_moral_check_log,
)


@add_error_handler
def get_feedback_api_blueprint():
    return blueprint
