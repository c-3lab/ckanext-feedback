from flask import Blueprint

from ckanext.feedback.controllers import resource
from ckanext.feedback.views.error_handler import add_error_handler

blueprint = Blueprint('resource_comment', __name__, url_prefix='/resource_comment')

# Add target page URLs to rules and add each URL to the blueprint
rules = [
    (
        '/<resource_id>',
        'comment',
        resource.ResourceController.comment,
        {'methods': ['GET']},
    ),
    (
        '/<resource_id>/comment/new',
        'create_comment',
        resource.ResourceController.create_comment,
        {'methods': ['POST']},
    ),
    (
        '/<resource_id>/comment/suggested',
        'suggested_comment',
        resource.ResourceController.suggested_comment,
        {'methods': ['GET', 'POST']},
    ),
    (
        '/<resource_id>/comment/check',
        'check_comment',
        resource.ResourceController.check_comment,
        {'methods': ['GET', 'POST']},
    ),
    (
        '/<resource_id>/comment/approve',
        'approve_comment',
        resource.ResourceController.approve_comment,
        {'methods': ['POST']},
    ),
    (
        '/<resource_id>/comment/reply',
        'reply',
        resource.ResourceController.reply,
        {'methods': ['POST']},
    ),
]
for rule, endpoint, view_func, *others in rules:
    options = next(iter(others), {})
    blueprint.add_url_rule(rule, endpoint, view_func, **options)


@add_error_handler
def get_resource_comment_blueprint():
    return blueprint
