from ckan import plugins
from ckan.common import config
from ckan.plugins import toolkit

from ckanext.feedback.command import feedback
from ckanext.feedback.views import utilization

from ckanext.feedback.command import feedback

class FeedbackPlugin(plugins.SingletonPlugin):
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
