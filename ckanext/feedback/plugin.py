import json
from types import SimpleNamespace

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

        # get path to the feedback_config.json file
        # open the file and load the settings
        try:
            feedback_config_path = config.get('ckan.feedback.config_file', '/etc/ckan')
            with open(f'{feedback_config_path}/feedback_config.json') as json_file:
                feedback_config = json.load(
                    json_file, object_hook=lambda d: SimpleNamespace(**d)
                ).modules
                self.is_feedback_config_file = True

                # the settings related to downloads module
                try:
                    config['ckan.feedback.downloads.enable'] = (
                        feedback_config.downloads.enable
                    )
                    config['ckan.feedback.downloads.enable_orgs'] = (
                        feedback_config.downloads.enable_orgs
                    )
                except AttributeError as e:
                    toolkit.error_shout(e)

                # the settings related to resources module
                try:
                    config['ckan.feedback.resources.enable'] = (
                        feedback_config.resources.enable
                    )
                    config['ckan.feedback.resources.enable_orgs'] = (
                        feedback_config.resources.enable_orgs
                    )
                except AttributeError as e:
                    toolkit.error_shout(e)

                # the settings related to resources comments module
                try:
                    config[
                        'ckan.feedback.resources.comment.repeat_post_limit.enable'
                    ] = feedback_config.resources.comments.repeat_post_limit.enable
                    config[
                        'ckan.feedback.resources.comment.repeat_post_limit.enable_orgs'
                    ] = feedback_config.resources.comments.repeat_post_limit.enable_orgs
                except AttributeError as e:
                    toolkit.error_shout(e)

                # the settings related to resource rating module
                try:
                    config['ckan.feedback.resources.comment.rating.enable'] = (
                        feedback_config.resources.comments.rating.enable
                    )
                    config['ckan.feedback.resources.comment.rating.enable_orgs'] = (
                        feedback_config.resources.comments.rating.enable_orgs
                    )
                except AttributeError as e:
                    toolkit.error_shout(e)

                # the settings related to utilizations module
                try:
                    config['ckan.feedback.utilizations.enable'] = (
                        feedback_config.utilizations.enable
                    )
                    config['ckan.feedback.utilizations.enable_orgs'] = (
                        feedback_config.utilizations.enable_orgs
                    )
                except AttributeError as e:
                    toolkit.error_shout(e)

        except FileNotFoundError:
            toolkit.error_shout('The feedback config file not found')
            self.is_feedback_config_file = False
        except json.JSONDecodeError:
            toolkit.error_shout('The feedback config file not decoded correctly')

    # IClick

    def get_commands(self):
        return [feedback.feedback]

    # IBlueprint

    # Return a flask Blueprint object to be registered by the extension
    def get_blueprint(self):
        blueprints = []
        if config.get('ckan.feedback.downloads.enable', True):
            blueprints.append(download.get_download_blueprint())
        if config.get('ckan.feedback.resources.enable', True):
            blueprints.append(resource.get_resource_comment_blueprint())
        if config.get('ckan.feedback.utilizations.enable', True):
            blueprints.append(utilization.get_utilization_blueprint())
        blueprints.append(management.get_management_blueprint())
        return blueprints

    # Check production.ini settings
    # Enable/disable the download module
    def is_enabled_downloads_org(self, org_id):
        enable = config.get('ckan.feedback.downloads.enable', True)
        if not self.is_feedback_config_file:
            return toolkit.asbool(enable)
        enable_org = org_id in config.get('ckan.feedback.downloads.enable_orgs', [])
        downloads_enable = enable and enable_org
        return toolkit.asbool(downloads_enable or not self.is_feedback_config_file)

    def is_enabled_downloads(self):
        enable = config.get('ckan.feedback.downloads.enable', True)
        return toolkit.asbool(enable)

    # Enable/disable the resources module
    def is_enabled_resources_org(self, org_id):
        enable = config.get('ckan.feedback.resources.enable', True)
        if not self.is_feedback_config_file:
            return toolkit.asbool(enable)
        enable_org = org_id in config.get('ckan.feedback.resources.enable_orgs', [])
        resources_enable = enable and enable_org
        return toolkit.asbool(resources_enable or not self.is_feedback_config_file)

    def is_enabled_resources(self):
        enable = config.get('ckan.feedback.resources.enable', True)
        return toolkit.asbool(enable)

    # Enable/disable the utilizations module
    def is_enabled_utilizations_org(self, org_id):
        enable = config.get('ckan.feedback.utilizations.enable', True)
        if not self.is_feedback_config_file:
            return toolkit.asbool(enable)
        enable_org = org_id in config.get('ckan.feedback.utilizations.enable_orgs', [])
        utilizations_enable = enable and enable_org
        return toolkit.asbool(utilizations_enable or not self.is_feedback_config_file)

    def is_enabled_utilizations(self):
        enable = config.get('ckan.feedback.utilizations.enable', True)
        return toolkit.asbool(enable)

    # Enable/disable repeat posting on a single resource
    def is_disabled_repeat_post_on_resource_org(self, org_id):
        enable = config.get(
            'ckan.feedback.resources.comment.repeat_post_limit.enable', False
        )
        if not self.is_feedback_config_file:
            return toolkit.asbool(enable)
        enable_org = org_id in config.get(
            'ckan.feedback.resources.comment.repeat_post_limit.enable_orgs',
            [],
        )
        repeat_post_limit_enable = enable and enable_org
        return toolkit.asbool(repeat_post_limit_enable)

    def is_disabled_repeat_post_on_resource(self):
        enable = config.get(
            'ckan.feedback.resources.comment.repeat_post_limit.enable', False
        )
        return toolkit.asbool(enable)

    # Enable/disable the rating function
    def is_enabled_rating_org(self, org_id):
        enable = config.get('ckan.feedback.resources.comment.rating.enable', False)
        if not self.is_feedback_config_file:
            return toolkit.asbool(enable)
        enable_org = org_id in config.get(
            'ckan.feedback.resources.comment.rating.enable_orgs', []
        )
        rating_enable = enable and enable_org
        return toolkit.asbool(rating_enable)

    def is_enabled_rating(self):
        enable = config.get('ckan.feedback.resources.comment.rating.enable', False)
        return toolkit.asbool(enable)

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'is_enabled_downloads_org': self.is_enabled_downloads_org,
            'is_enabled_downloads': self.is_enabled_downloads,
            'is_enabled_resources_org': self.is_enabled_resources_org,
            'is_enabled_resources': self.is_enabled_resources,
            'is_enabled_utilizations_org': self.is_enabled_utilizations_org,
            'is_enabled_utilizations': self.is_enabled_utilizations,
            'is_disabled_repeat_post_on_resource_org': (
                self.is_disabled_repeat_post_on_resource_org
            ),
            'is_disabled_repeat_post_on_resource': (
                self.is_disabled_repeat_post_on_resource
            ),
            'is_enabled_rating': self.is_enabled_rating,
            'is_enabled_rating_org': self.is_enabled_rating_org,
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
