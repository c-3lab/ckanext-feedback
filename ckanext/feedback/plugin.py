import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.feedback.command import feedback

class FeedbackPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IClick)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic',
            'feedback')

    def get_commands(self):
        return [feedback.feedback]
