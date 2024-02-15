from ckan import plugins
from ckan.common import config
from ckan.lib.plugins import DefaultTranslation
from ckan.plugins import toolkit

from ckanext.feedback.command import feedback
from ckanext.feedback.services.common import check
from ckanext.feedback.services.download import summary as download_summary_service
from ckanext.feedback.services.management import comments as management_comments_service
from ckanext.feedback.services.resource import comment as comment_service
from ckanext.feedback.services.resource import summary as resource_summary_service
from ckanext.feedback.services.utilization import summary as utilization_summary_service
from ckanext.feedback.views import download, management, resource, utilization


class FeedbackPlugin(plugins.SingletonPlugin, DefaultTranslation):
    # Declare class implements
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)

    # IConfigurer

    def update_config(self, config):
        # Add this plugin's directories to CKAN's extra paths, so that
        # CKAN will use this plugin's custom files.
        # Paths are relative to this plugin.py file.
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('assets', 'feedback')

    # IClick

    def get_commands(self):
        return [feedback.feedback]

    # IBlueprint

    # Return a flask Blueprint object to be registered by the extension
    def get_blueprint(self):
        blueprints = []
        if self.is_enabled_downloads():
            blueprints.append(download.get_download_blueprint())
        if self.is_enabled_resources():
            blueprints.append(resource.get_resource_comment_blueprint())
        if self.is_enabled_utilizations():
            blueprints.append(utilization.get_utilization_blueprint())
        blueprints.append(management.get_management_blueprint())
        return blueprints

    # Check production.ini settings
    # Enable/disable the download module
    def is_enabled_downloads(self):
        return toolkit.asbool(config.get('ckan.feedback.downloads.enable', True))

    # Enable/disable the resources module
    def is_enabled_resources(self):
        return toolkit.asbool(config.get('ckan.feedback.resources.enable', True))

    # Enable/disable the utilizations module
    def is_enabled_utilizations(self):
        return toolkit.asbool(config.get('ckan.feedback.utilizations.enable', True))

    # Enable/disable repeated posting on a single resource
    def is_disabled_repeated_post_on_resource(self):
        return toolkit.asbool(
            config.get(
                'ckan.feedback.resources.comment.repeated_post_limit.enable', False
            )
        )

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'is_enabled_downloads': self.is_enabled_downloads,
            'is_enabled_resources': self.is_enabled_resources,
            'is_enabled_utilizations': self.is_enabled_utilizations,
            'is_disabled_repeated_post_on_resource': (
                self.is_disabled_repeated_post_on_resource
            ),
            'is_organization_admin': check.is_organization_admin,
            'has_organization_admin_role': check.has_organization_admin_role,
            'get_resource_downloads': download_summary_service.get_resource_downloads,
            'get_package_downloads': download_summary_service.get_package_downloads,
            'get_resource_utilizations': (
                utilization_summary_service.get_resource_utilizations
            ),
            'get_package_utilizations': (
                utilization_summary_service.get_package_utilizations
            ),
            'get_resource_issue_resolutions': (
                utilization_summary_service.get_resource_issue_resolutions
            ),
            'get_package_issue_resolutions': (
                utilization_summary_service.get_package_issue_resolutions
            ),
            'get_comment_reply': comment_service.get_comment_reply,
            'get_resource_comments': resource_summary_service.get_resource_comments,
            'get_package_comments': resource_summary_service.get_package_comments,
            'get_resource_rating': resource_summary_service.get_resource_rating,
            'get_package_rating': resource_summary_service.get_package_rating,
            'get_organization': management_comments_service.get_organization,
        }
