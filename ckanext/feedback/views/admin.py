from flask import Blueprint

from ckanext.feedback.controllers import admin
from ckanext.feedback.views.error_handler import add_error_handler

blueprint = Blueprint('feedback', __name__, url_prefix='/feedback')

# Add target page URLs to rules and add each URL to the blueprint
rules = [
    (
        '/admin',
        'admin',
        admin.AdminController.admin,
        {'methods': ['GET']},
    ),
    (
        '/admin/approval-and-delete',
        'approval-and-delete',
        admin.AdminController.approval_and_delete,
        {'methods': ['GET']},
    ),
    (
        '/admin/approve_target',
        'approve_target',
        admin.AdminController.approve_target,
        {'methods': ['POST']},
    ),
    (
        '/admin/delete_target',
        'delete_target',
        admin.AdminController.delete_target,
        {'methods': ['POST']},
    ),
    (
        '/admin/aggregation',
        'aggregation',
        admin.AdminController.aggregation,
        {'methods': ['GET']},
    ),
    (
        '/admin/aggregation/download_monthly',
        'download_monthly',
        admin.AdminController.download_monthly,
        {'methods': ['GET']},
    ),
    (
        '/admin/aggregation/download_yearly',
        'download_yearly',
        admin.AdminController.download_yearly,
        {'methods': ['GET']},
    ),
    (
        '/admin/aggregation/download_all_time',
        'download_all_time',
        admin.AdminController.download_all_time,
        {'methods': ['GET']},
    ),
]
for rule, endpoint, view_func, *others in rules:
    options = next(iter(others), {})
    blueprint.add_url_rule(rule, endpoint, view_func, **options)


@add_error_handler
def get_admin_blueprint():
    return blueprint
