from flask import Blueprint

from ckanext.feedback.controllers import management
from ckanext.feedback.views.error_handler import add_error_handler

blueprint = Blueprint('management', __name__, url_prefix='/management')

# Add target page URLs to rules and add each URL to the blueprint
rules = [
    (
        '/comments',
        'comments',
        management.ManagementController.admin,
        {'methods': ['GET']},
    ),
    # (
    #     '/comments',
    #     'comments',
    #     management.ManagementController.comments,
    #     {'methods': ['GET']},
    # ),
    (
        '/approve_bulk_utilization_comments',
        'approve_bulk_utilization_comments',
        management.ManagementController.approve_bulk_utilization_comments,
        {'methods': ['POST']},
    ),
    (
        '/approve_bulk_resource_comments',
        'approve_bulk_resource_comments',
        management.ManagementController.approve_bulk_resource_comments,
        {'methods': ['POST']},
    ),
    (
        '/delete_bulk_utilization_comments',
        'delete_bulk_utilization_comments',
        management.ManagementController.delete_bulk_utilization_comments,
        {'methods': ['POST']},
    ),
    (
        '/delete_bulk_resource_comments',
        'delete_bulk_resource_comments',
        management.ManagementController.delete_bulk_resource_comments,
        {'methods': ['POST']},
    ),
]
for rule, endpoint, view_func, *others in rules:
    options = next(iter(others), {})
    blueprint.add_url_rule(rule, endpoint, view_func, **options)


@add_error_handler
def get_management_blueprint():
    return blueprint
