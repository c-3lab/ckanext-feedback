import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import config
from flask import Blueprint

import ckanext.feedback.controllers.utilization as utilization
import ckanext.feedback.services.utilization.details as detailService
import ckanext.feedback.services.utilization.search as searchService
from ckanext.feedback.command import feedback

# Render HTML pages
# utilization/details.html
def details():
    return tk.render('utilization/details.html')
# utilization/registration.html
def registration():
    return tk.render('utilization/registration.html')
# utilization/comment_approval.html
def comment_approval():
    return tk.render('utilization/comment_approval.html')
# utilization/recommentview.html
def comment():
    return tk.render('utilization/comment.html')
# utilization/search.html
def search():
    return tk.render('utilization/search.html')

class FeedbackPlugin(plugins.SingletonPlugin):
    # Declare class implements
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)

    def update_config(self, config):
        # Add this plugin's directories to CKAN's extra paths, so that
        # CKAN will use this plugin's custom files.
        # Paths are relative to this plugin.py file.
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('assets', 'feedback')

    # Return a flask Blueprint object to be registered by the extension
    def get_blueprint(self):
        blueprint = Blueprint('search', self.__module__)
        # Add target page URLs to rules and add each URL to the blueprint
        rules = [
            ('/utilization/details', 'details',
                utilization.UtilizationController.details),
            (
                '/utilization/registration', 'registration',
                utilization.UtilizationController.registration,
            ),
            (
                '/utilization/comment_approval', 'comment_approval',
                utilization.UtilizationController.comment_approval
            ),
            (
                '/utilization/comment', 'comment',
                utilization.UtilizationController.comment
            ),
            (
                '/utilization/search', 'search',
                utilization.UtilizationController.search
            ),
        ]
        for rule in rules:
            blueprint.add_url_rule(*rule)

        return blueprint

    def get_commands(self):
        return [feedback.feedback]

        # Check production.ini settings
    # Enable/disable the download module
    def enable_downloads(self):
        return toolkit.asbool(config.get('ckan.feedback.downloads.enable', False))

    # Enable/disable the resources module
    def enable_resources(self):
        return toolkit.asbool(config.get('ckan.feedback.resources.enable', False))

    # Enable/disable the utilizations module
    def enable_utilizations(self):
        return toolkit.asbool(config.get('ckan.feedback.utilizations.enable', False))

    def get_helpers(self):
        '''Register the most_popular_groups() function above as a template
        helper function.

        '''
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {
            'enable_downloads': FeedbackPlugin.enable_downloads,
            'enable_resources': FeedbackPlugin.enable_resources,
            'enable_utilizations': FeedbackPlugin.enable_utilizations,
            'get_utilizations': searchService.get_utilizations,
            'keep_keyword': searchService.keep_keyword,
            'get_utilization_details': detailService.get_utilization_details
        }
