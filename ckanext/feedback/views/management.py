from flask import Blueprint

from ckanext.feedback.controllers import management
from ckanext.feedback.views.error_handler import add_error_handler

blueprint = Blueprint('feedback', __name__, url_prefix='/feedback')

# Add target page URLs to rules and add each URL to the blueprint
rules = [
    (
        '/management/approval-delete',
        'approval-delete',
        management.ManagementController.admin,
        {'methods': ['GET']},
    ),
    (
        '/management/approve_bulk_target',
        'approve_bulk_target',
        management.ManagementController.approve_bulk_target,
        {'methods': ['POST']},
    ),
    (
        '/management/delete_bulk_target',
        'delete_bulk_target',
        management.ManagementController.delete_bulk_target,
        {'methods': ['POST']},
    ),
]
for rule, endpoint, view_func, *others in rules:
    options = next(iter(others), {})
    blueprint.add_url_rule(rule, endpoint, view_func, **options)


@add_error_handler
def get_management_blueprint():
    return blueprint
