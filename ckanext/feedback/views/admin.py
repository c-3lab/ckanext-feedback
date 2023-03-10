from flask import Blueprint

from ckanext.feedback.controllers import admin
from ckanext.feedback.views.error_handler import add_error_handler

blueprint = Blueprint('admin', __name__, url_prefix='/admin')

# Add target page URLs to rules and add each URL to the blueprint
rules = [
    (
        '/comments',
        'comments',
        admin.AdminController.comments,
    ),
]
for rule in rules:
    blueprint.add_url_rule(*rule)


@add_error_handler
def get_admin_blueprint():
    return blueprint
