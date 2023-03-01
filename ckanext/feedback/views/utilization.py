from flask import Blueprint

from ckanext.feedback.controllers import utilization
from ckanext.feedback.views.error_handler import add_error_handler

blueprint = Blueprint('utilization', __name__, url_prefix='/utilization')

# Add target page URLs to rules and add each URL to the blueprint
rules = [
    (
        '/details',
        'details',
        utilization.UtilizationController.details,
    ),
    (
        '/registration',
        'registration',
        utilization.UtilizationController.registration,
    ),
    (
        '/comment_approval',
        'comment_approval',
        utilization.UtilizationController.comment_approval,
    ),
    (
        '/comment',
        'comment',
        utilization.UtilizationController.comment,
    ),
    ('/search', 'search', utilization.UtilizationController.search),
]
for rule in rules:
    blueprint.add_url_rule(*rule)


@add_error_handler
def get_utilization_blueprint():
    return blueprint
