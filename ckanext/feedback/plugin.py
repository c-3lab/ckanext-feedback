import logging
from typing import Any, Dict, Optional

import ckan.model as model
from ckan import plugins
from ckan.common import _, config
from ckan.lib.plugins import DefaultTranslation
from ckan.plugins import toolkit
from ckan.types import PUploader

from ckanext.feedback.command import feedback
from ckanext.feedback.components.comment import CommentComponent
from ckanext.feedback.controllers.api import ranking as get_action_controllers
from ckanext.feedback.controllers.resource import ResourceController
from ckanext.feedback.services.common import check
from ckanext.feedback.services.common.config import FeedbackConfig
from ckanext.feedback.services.common.upload import FeedbackUpload
from ckanext.feedback.services.download import summary as download_summary_service
from ckanext.feedback.services.organization import organization as organization_service
from ckanext.feedback.services.resource import comment as comment_service
from ckanext.feedback.services.resource import likes as resource_likes_service
from ckanext.feedback.services.resource import summary as resource_summary_service
from ckanext.feedback.services.utilization import details as utilization_details_service
from ckanext.feedback.services.utilization import summary as utilization_summary_service
from ckanext.feedback.views import admin, api, download, likes, resource, utilization

log = logging.getLogger(__name__)


class FeedbackPlugin(plugins.SingletonPlugin, DefaultTranslation):
    # Declare class implements
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IUploader, inherit=True)

    # IConfigurer

    def update_config(self, config):
        # Add this plugin's directories to CKAN's extra paths, so that
        # CKAN will use this plugin's custom files.
        # Paths are relative to this plugin.py file.
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('assets', 'feedback')

        # load the settings from feedback config json
        self.fb_config = FeedbackConfig()
        self.fb_config.load_feedback_config()

    # IClick

    def get_commands(self):
        return [feedback.feedback]

    # IBlueprint

    # Return a flask Blueprint object to be registered by the extension
    def get_blueprint(self):
        blueprints = []
        cfg = getattr(self, 'fb_config', FeedbackConfig())

        # Register download-related blueprints
        if cfg.download.is_enable():
            if plugins.plugin_loaded('datastore'):
                from ckanext.feedback.views.datastore_download import (
                    get_datastore_download_blueprint,
                )

                # Insert at the beginning for slight performance optimization
                # since before_app_request hooks run in registration order
                blueprints.insert(0, get_datastore_download_blueprint())
            blueprints.append(download.get_download_blueprint())

        if cfg.resource_comment.is_enable():
            blueprints.append(resource.get_resource_comment_blueprint())
        if cfg.utilization.is_enable():
            blueprints.append(utilization.get_utilization_blueprint())
        if cfg.like.is_enable():
            blueprints.append(likes.get_likes_blueprint())
        blueprints.append(admin.get_admin_blueprint())
        blueprints.append(api.get_feedback_api_blueprint())
        return blueprints

    def is_base_public_folder_bs3(self):
        base_templates_folder = config.get('ckan.base_public_folder', 'public')
        return base_templates_folder == 'public-bs3'

    # ITemplateHelpers

    def get_helpers(self):
        cfg = getattr(self, 'fb_config', FeedbackConfig())
        return {
            'is_enabled_downloads': cfg.download.is_enable,
            'is_enable_modal': cfg.download.modal.is_enable,
            'is_enabled_resources': cfg.resource_comment.is_enable,
            'is_enabled_utilizations': cfg.utilization.is_enable,
            'is_enabled_utilization_comment_image_attachment': (
                cfg.utilization_comment.image_attachment.is_enable
            ),
            'is_enabled_likes': cfg.like.is_enable,
            'is_disabled_repeat_post_on_resource': (
                cfg.resource_comment.repeat_post_limit.is_enable
            ),
            'is_enabled_rating': cfg.resource_comment.rating.is_enable,
            'is_enabled_image_attachment': (
                cfg.resource_comment.image_attachment.is_enable
            ),
            'is_organization_admin': check.is_organization_admin,
            'is_base_public_folder_bs3': self.is_base_public_folder_bs3,
            'has_organization_admin_role': check.has_organization_admin_role,
            'user_has_organization_admin_role': check.user_has_organization_admin_role,
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
            'get_utilization_comment_replies_for_display': (
                utilization_details_service.get_utilization_comment_replies_for_display
            ),
            'get_comment_replies': comment_service.get_comment_replies,
            'get_comment_replies_for_display': (
                comment_service.get_comment_replies_for_display
            ),
            'get_resource_comments': resource_summary_service.get_resource_comments,
            'get_package_comments': resource_summary_service.get_package_comments,
            'get_resource_rating': resource_summary_service.get_resource_rating,
            'get_package_rating': resource_summary_service.get_package_rating,
            'get_resource_like_count': resource_likes_service.get_resource_like_count,
            'get_package_like_count': resource_likes_service.get_package_like_count,
            'get_organization': organization_service.get_organization,
            'is_enabled_feedback_recaptcha': cfg.recaptcha.is_enable,
            'is_feedback_recaptcha_force_all': cfg.recaptcha.force_all.get,
            'get_feedback_recaptcha_publickey': cfg.recaptcha.publickey.get,
            'is_resource_reply_open': cfg.resource_comment.reply_open.is_enable,
            'is_utilization_reply_open': cfg.utilization_comment.reply_open.is_enable,
            'like_status': ResourceController.like_status,
            'create_category_icon': CommentComponent.create_category_icon,
            'CommentComponent': CommentComponent,
        }

    # IPackageController

    def before_dataset_view(self, pkg_dict: Dict[str, Any]) -> Dict[str, Any]:
        package_id = pkg_dict['id']
        owner_org = model.Package.get(package_id).owner_org
        cfg = getattr(self, 'fb_config', FeedbackConfig())

        if not pkg_dict['extras']:
            pkg_dict['extras'] = []

        def add_pkg_dict_extras(key: str, value: str):
            pkg_dict['extras'].append({'key': key, 'value': value})

        if cfg.download.is_enable(owner_org):
            add_pkg_dict_extras(
                key=_('Downloads'),
                value=download_summary_service.get_package_downloads(package_id),
            )

        if cfg.utilization.is_enable(owner_org):
            add_pkg_dict_extras(
                key=_('Utilizations'),
                value=(
                    utilization_summary_service.get_package_utilizations(package_id)
                ),
            )
            add_pkg_dict_extras(
                key=_('Issue Resolutions'),
                value=(
                    utilization_summary_service.get_package_issue_resolutions(
                        package_id
                    )
                ),
            )

        if cfg.resource_comment.is_enable(owner_org):
            add_pkg_dict_extras(
                key=_('Comments'),
                value=resource_summary_service.get_package_comments(package_id),
            )
            if cfg.resource_comment.rating.is_enable(owner_org):
                add_pkg_dict_extras(
                    key=_('Rating'),
                    value=round(
                        resource_summary_service.get_package_rating(package_id), 1
                    ),
                )

        if cfg.like.is_enable(owner_org):
            add_pkg_dict_extras(
                key=_('Number of Likes'),
                value=resource_likes_service.get_package_like_count(package_id),
            )

        return pkg_dict

    # IResourceController

    def before_resource_show(self, resource_dict: Dict[str, Any]) -> Dict[str, Any]:
        owner_org = model.Package.get(resource_dict['package_id']).owner_org
        resource_id = resource_dict['id']
        cfg = getattr(self, 'fb_config', FeedbackConfig())

        # If datastore plugin is not loaded, set datastore_active to False
        # to prevent template errors when trying to build datastore.dump URLs
        if not plugins.plugin_loaded('datastore'):
            if resource_dict.get('datastore_active', False):
                resource_dict['datastore_active'] = False

        if cfg.download.is_enable(owner_org):
            if _('Downloads') != 'Downloads':
                resource_dict.pop('Downloads', None)
            resource_dict[_('Downloads')] = (
                download_summary_service.get_resource_downloads(resource_id)
            )

        if cfg.utilization.is_enable(owner_org):
            if _('Utilizations') != 'Utilizations':
                resource_dict.pop('Utilizations', None)
            resource_dict[_('Utilizations')] = (
                utilization_summary_service.get_resource_utilizations(resource_id)
            )
            if _('Issue Resolutions') != 'Issue Resolutions':
                resource_dict.pop('Issue Resolutions', None)
            resource_dict[_('Issue Resolutions')] = (
                utilization_summary_service.get_resource_issue_resolutions(resource_id)
            )

        if cfg.resource_comment.is_enable(owner_org):
            if _('Comments') != 'Comments':
                resource_dict.pop('Comments', None)
            resource_dict[_('Comments')] = (
                resource_summary_service.get_resource_comments(resource_id)
            )
            if cfg.resource_comment.rating.is_enable(owner_org):
                if _('Rating') != 'Rating':
                    resource_dict.pop('Rating', None)
                resource_dict[_('Rating')] = round(
                    resource_summary_service.get_resource_rating(resource_id), 1
                )

        if cfg.like.is_enable(owner_org):
            if _('Number of Likes') != 'Number of Likes':
                resource_dict.pop('Number of Likes', None)
            resource_dict[_('Number of Likes')] = (
                resource_likes_service.get_resource_like_count(resource_id)
            )

        return resource_dict

    def get_actions(self):
        return {
            'datasets_ranking': get_action_controllers.datasets_ranking,
        }

    # IUploader

    def get_uploader(
        self, upload_to: str, old_filename: Optional[str]
    ) -> Optional[PUploader]:
        if upload_to.startswith("feedback_"):
            return FeedbackUpload(upload_to, old_filename)
        return None
