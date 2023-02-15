import ckan.plugins as p
import ckan.plugins.toolkit as tk
from flask import Blueprint
from ckan.config.routing import SubMapper
import ckanext.feedback.services.utilization.search as searchService
from ckan.common import config
from flask import Blueprint  # type: ignore

import ckanext.feedback.controllers.utilization as utilization
import ckanext.feedback.services.utilization.search \
    as searchService  # type: ignore
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

class FeedbackPlugin(p.SingletonPlugin):
    # Declare class implements
    p.implements(p.IConfigurer)
    p.implements(p.IClick)
    p.implements(p.IBlueprint)
    p.implements(p.ITemplateHelpers)

    def update_config(self, config):
        # Add this plugin's directories to CKAN's extra paths, so that
        # CKAN will use this plugin's custom files.
        # Paths are relative to this plugin.py file.
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('assets', 'feedback')

        # Retrieve the value for the "ckan.feedback.substitute_templates"
        # setting from the Config file (/etc/ckan/production.ini) and
        # return it as a bool.
        # If the "ckan.feedback.substitute_templates" setting doesn't exist
        # return False
        substitute_templates = tk.asbool(
            config.get('ckan.feedback.substitute_templates', False)
        )

        # If substitute_templates is True, add the feedback directories below
        # to CKAN's extra paths
        if substitute_templates:
            # Add this plugin's directories to CKAN's extra paths, so that CKAN will use this plugin's custom files.
            # Paths are relative to this plugin.py file.
            tk.add_template_directory(config, 'templates')
            tk.add_public_directory(config, 'public')
            tk.add_resource('assets', 'feedback')

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
    # Show/hide the main screen search bar
    def show_search_bar(self):
        return tk.asbool(config.get(
            'ckan.feedback.utilization.show_search_bar', False))

    # Show/hide the status selection checkboxes
    def show_status_selection(self):
        return tk.asbool(
            config.get(
                'ckan.feedback.utilization.show_status_selection', False)
        )

    # Show/hide the record count
    def show_record_count(self):
        return tk.asbool(
            config.get(
                'ckan.feedback.utilization.show_record_count', False)
        )

    # Show/hide the record table
    def show_record_table(self):
        return tk.asbool(
            config.get(
                'ckan.feedback.utilization.show_record_table', False)
        )

    # Show/hide the record table issue resolution badge
    def show_record_table_badge(self):
        return tk.asbool(
            config.get(
                'ckan.feedback.utilization.show_record_table_badge', False)
        )

    # Show/hide the record table issue resolution count
    def show_record_table_issue_resolution_count(self):
        return tk.asbool(
            config.get(
                'ckan.feedback.utilization.'
                'show_record_table_issue_resolution_count',
                False,
            )
        )

    def get_helpers(self):
        '''Register the most_popular_groups() function above as a template
        helper function.

        '''
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {
            'show_search_bar': FeedbackPlugin.show_search_bar,
            'show_status_selection': FeedbackPlugin.show_status_selection,
            'show_record_count': FeedbackPlugin.show_record_count,
            'show_record_table': FeedbackPlugin.show_record_table,
            'show_record_table_badge': FeedbackPlugin.show_record_table_badge,
            'show_record_table_issue_resolution_count':
                FeedbackPlugin.show_record_table_issue_resolution_count,
            'get_data': searchService.get_data,
            'keep_keyword': searchService.keep_keyword
        }
