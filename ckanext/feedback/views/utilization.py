from flask import Blueprint

from ckanext.feedback.controllers import utilization

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
        '/edit',
        'edit',
        utilization.UtilizationController.edit,
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
    utilization_blueprint.add_url_rule(*rule, methods=['GET', 'POST'])
