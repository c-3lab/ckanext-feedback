import logging

from flask import Blueprint

from ckanext.feedback.controllers import resource
from ckanext.feedback.views.error_handler import add_error_handler

log = logging.getLogger(__name__)

blueprint = Blueprint(
    'likes',
    __name__,
    url_prefix='/dataset/<package_name>/resource',
)

rules = [
    (
        '<resource_id>/like_status',
        'like_status',
        resource.ResourceController.like_status,
        {'methods': ['POST']},
    ),
    (
        '<resource_id>/like_toggle',
        'like_toggle',
        resource.ResourceController.like_toggle,
        {'methods': ['POST']},
    ),
]

for rule, endpoint, view_func, *others in rules:
    options = next(iter(others), {})
    blueprint.add_url_rule(rule, endpoint, view_func, **options)


@add_error_handler
def get_likes_blueprint():
    return blueprint
