from flask import Blueprint

from ckanext.feedback.controllers import utilization
from ckanext.feedback.views.error_handler import add_error_handler

blueprint = Blueprint('utilization', __name__, url_prefix='/utilization')

# Add target page URLs to rules and add each URL to the blueprint
rules = [
    ('/search', 'search', utilization.UtilizationController.search),
    (
        '/registration/<resource_id>',
        'registration',
        utilization.UtilizationController.registration,
    ),
    (
        '/registration/<resource_id>/create_summary',
        'create_summary',
        utilization.UtilizationController.create_summary,
    ),
    (
        '/<utilization_id>',
        'details',
        utilization.UtilizationController.details,
    ),
    (
        '/<utilization_id>/approve',
        'approve',
        utilization.UtilizationController.approve,
    ),
    (
        '/<utilization_id>/create_comment',
        'create_comment',
        utilization.UtilizationController.create_comment,
    ),
    (
        '/<utilization_id>/approve_comment',
        'approve_comment',
        utilization.UtilizationController.approve_comment,
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
]
for rule in rules:
    blueprint.add_url_rule(*rule, methods=['GET', 'POST'])


@add_error_handler
def get_utilization_blueprint():
    return blueprint
