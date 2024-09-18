from flask import Blueprint

from ckanext.feedback.controllers import utilization
from ckanext.feedback.views.error_handler import add_error_handler

blueprint = Blueprint('utilization', __name__, url_prefix='/utilization')

# Add target page URLs to rules and add each URL to the blueprint
rules = [
    (
        '/search',
        'search',
        utilization.UtilizationController.search,
        {'methods': ['GET']},
    ),
    ('/new', 'new', utilization.UtilizationController.new, {'methods': ['GET']}),
    ('/new', 'create', utilization.UtilizationController.create, {'methods': ['POST']}),
    (
        '/<utilization_id>',
        'details',
        utilization.UtilizationController.details,
        {'methods': ['GET']},
    ),
    (
        '/<utilization_id>/approve',
        'approve',
        utilization.UtilizationController.approve,
        {'methods': ['POST']},
    ),
    (
        '/<utilization_id>/comment/new',
        'create_comment',
        utilization.UtilizationController.create_comment,
        {'methods': ['POST']},
    ),
    (
        '/<utilization_id>/comment/suggested',
        'suggested_comment',
        utilization.UtilizationController.suggested_comment,
        {'methods': ['GET', 'POST']},
    ),
    (
        '/<utilization_id>/comment/check',
        'check_comment',
        utilization.UtilizationController.check_comment,
        {'methods': ['GET', 'POST']},
    ),
    (
        '/<utilization_id>/comment/<comment_id>/approve',
        'approve_comment',
        utilization.UtilizationController.approve_comment,
        {'methods': ['POST']},
    ),
    (
        '/<utilization_id>/edit',
        'edit',
        utilization.UtilizationController.edit,
        {'methods': ['GET']},
    ),
    (
        '/<utilization_id>/edit',
        'update',
        utilization.UtilizationController.update,
        {'methods': ['POST']},
    ),
    (
        '/<utilization_id>/delete',
        'delete',
        utilization.UtilizationController.delete,
        {'methods': ['POST']},
    ),
    (
        '/<utilization_id>/issue_resolution/new',
        'create_issue_resolution',
        utilization.UtilizationController.create_issue_resolution,
        {'methods': ['POST']},
    ),
]
for rule, endpoint, view_func, *others in rules:
    options = next(iter(others), {})
    blueprint.add_url_rule(rule, endpoint, view_func, **options)


@add_error_handler
def get_utilization_blueprint():
    return blueprint
