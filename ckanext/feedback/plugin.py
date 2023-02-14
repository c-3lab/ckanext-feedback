import ckan.plugins as p
import ckan.plugins.toolkit as tk
from flask import Blueprint
from ckan.config.routing import SubMapper
import ckanext.feedback.services.utilization.search as searchService
from ckan.common import config
from flask import Blueprint  # type: ignore

import ckanext.feedback.controllers.utilization as utilization
import ckanext.feedback.services.utilization.search as searchService  # type: ignore
from ckanext.feedback.command import feedback

from ckanext.feedback.command import feedback

class FeedbackPlugin(p.SingletonPlugin):
    # Declare class implements
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IClick)

    def update_config(self, config):
        # Add this plugin's directories to CKAN's extra paths, so that
        # CKAN will use this plugin's custom files.
        # Paths are relative to this plugin.py file.
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('assets', 'feedback')

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic',
            'feedback')

    def get_commands(self):
        return [feedback.feedback]
