import json
import logging
import os
from abc import ABC, abstractmethod

from ckan.common import config
from ckan.plugins import toolkit
from werkzeug.utils import import_string

from ckanext.feedback.services.common.feedback_config_validator import (
    FEATURE_IMAGE_ATTACHMENT,
    FEATURE_MODAL,
    FEATURE_RATING,
    FEATURE_REPEAT_POST_LIMIT,
    FEATURE_REPLY_OPEN,
    FIELD_DISABLE_ORGS,
    FIELD_ENABLE,
    FIELD_ENABLE_ORGS,
    MODULE_DOWNLOADS,
    MODULE_LIKES,
    MODULE_MORAL_KEEPER_AI,
    MODULE_NOTICE,
    MODULE_RECAPTCHA,
    MODULE_RESOURCES,
    MODULE_UTILIZATIONS,
    SUBMODULE_COMMENTS,
    SUBMODULE_FEEDBACK_PROMPT,
    validate_feedback_config,
)
from ckanext.feedback.services.organization import organization as organization_service

log = logging.getLogger(__name__)

CONFIG_HANDLER_PATH = 'ckan.feedback.download_handler'
FB_CONF_KEY_MODULES = 'modules'


def download_handler():
    handler_path = config.get(CONFIG_HANDLER_PATH)
    if handler_path:
        handler = import_string(handler_path, silent=True)
    else:
        handler = None
        log.warning(f'Missing {CONFIG_HANDLER_PATH} config option.')

    return handler


class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


class FeedbackConfigInterface(ABC):
    @abstractmethod
    def load_config(self, feedback_config):  # pragma: no cover
        # Excluded from coverage because it cannot be directly tested and
        # must be implemented in subclasses.
        pass


class BaseConfig:
    def __init__(self, name: str, parent: list = None):
        self.default = None
        self.name = name
        self.ckan_conf_prefix = ['ckan', 'feedback']
        self.fb_conf_prefix = [FB_CONF_KEY_MODULES]
        self.conf_path = (parent or []) + [name]

    def get_ckan_conf_str(self):
        return '.'.join(self.ckan_conf_prefix + self.conf_path)

    def set_enable_and_enable_orgs_and_disable_orgs(self, module_config: dict = None):
        ckan_conf_str = self.get_ckan_conf_str()
        if module_config is None:
            config.pop(f"{ckan_conf_str}.{FIELD_ENABLE}", None)
            config.pop(f"{ckan_conf_str}.{FIELD_ENABLE_ORGS}", None)
            config.pop(f"{ckan_conf_str}.{FIELD_DISABLE_ORGS}", None)
            return

        enable = module_config.get(FIELD_ENABLE)
        enable_orgs = module_config.get(FIELD_ENABLE_ORGS)
        disable_orgs = module_config.get(FIELD_DISABLE_ORGS)

        config[f"{ckan_conf_str}.{FIELD_ENABLE}"] = enable
        if enable_orgs:
            config[f"{ckan_conf_str}.{FIELD_ENABLE_ORGS}"] = enable_orgs
        if disable_orgs:
            config[f"{ckan_conf_str}.{FIELD_DISABLE_ORGS}"] = disable_orgs

    def set_config(
        self,
        feedback_config: dict,
        ckan_conf_path: list = None,
        fb_conf_path: list = None,
    ):
        ckan_conf_path = ckan_conf_path or self.conf_path
        fb_conf_path = fb_conf_path or self.conf_path

        ckan_conf_path_str = '.'.join(self.ckan_conf_prefix + ckan_conf_path)
        value = feedback_config

        for key in self.fb_conf_prefix + fb_conf_path:
            try:
                value = value.get(key)
            except AttributeError as e:
                toolkit.error_shout(e)
        if value is not None:
            config[ckan_conf_path_str] = value

    def get(self):
        ck_conf_str = self.get_ckan_conf_str()
        return config.get(f"{ck_conf_str}", self.default)

    def is_enable(self, org_id=''):
        ck_conf_str = self.get_ckan_conf_str()
        # Retrieve the on/off value for the feature from the ini file
        enable = config.get(f"{ck_conf_str}.{FIELD_ENABLE}", self.default)

        try:
            # Convert the retrieved value to a boolean
            # (True, yes, on, 1, False, no, off, 0)
            enable = toolkit.asbool(enable)
        except ValueError:
            # Raise a ValidationError if conversion fails
            raise toolkit.ValidationError(
                {
                    "message": (
                        "The value of the \"enable\" key is invalid. "
                        "Please specify a boolean value such as "
                        "`true` or `false` for the \"enable\" key."
                    )
                }
            )

        # Return the value of the module or feature if it is off, if the
        # configuration file is missing, or if no organization is specified
        if not enable or not FeedbackConfig().is_feedback_config_file or not org_id:
            return enable

        # Retrieve the name of the specified organization
        organization = organization_service.get_organization_name_by_id(org_id)

        # Return False if the specified organization cannot be retrieved
        if not organization:
            return False

        # Retrieve the list of enabled organizations and disabled
        # organizations (loaded from feedback_config.json)
        enable_orgs = config.get(f"{ck_conf_str}.{FIELD_ENABLE_ORGS}")
        disable_orgs = config.get(f"{ck_conf_str}.{FIELD_DISABLE_ORGS}")

        # Return True if neither the list of enabled organizations
        # nor the list of disabled organizations exists
        if not enable_orgs and not disable_orgs:
            return enable

        # If both the list of enabled organizations and the list
        # of disabled organizations exist, turn off the organizations
        # in the disabled list and turn on the others
        if enable_orgs and disable_orgs:
            return organization.name not in disable_orgs

        if enable_orgs:
            # If only the list of enabled organizations exists,
            # turn on organizations in the enabled list and turn off the others
            return organization.name in enable_orgs
        else:
            # If only the list of disabled organizations exists,
            # turn off organizations in the disabled list and turn on the others
            return organization.name not in disable_orgs

    def get_enable_org_names(self):
        ck_conf_str = self.get_ckan_conf_str()
        enable = config.get(f"{ck_conf_str}.{FIELD_ENABLE}", self.default)

        if not enable:
            return []

        all_org_names = organization_service.get_organization_name_list()
        enable_orgs = config.get(f"{ck_conf_str}.{FIELD_ENABLE_ORGS}", [])
        disable_orgs = config.get(f"{ck_conf_str}.{FIELD_DISABLE_ORGS}", [])

        if disable_orgs:
            enable_orgs = [org for org in all_org_names if org not in disable_orgs]
            return enable_orgs

        if enable_orgs:
            return enable_orgs

        return all_org_names


class DownloadsConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__(MODULE_DOWNLOADS)
        self.default = True
        parents = self.conf_path + [SUBMODULE_FEEDBACK_PROMPT]
        self.modal = BaseConfig(FEATURE_MODAL, parents)
        self.modal.default = True

    def load_config(self, feedback_config):
        module_config = feedback_config.get(FB_CONF_KEY_MODULES, {}).get(
            MODULE_DOWNLOADS
        )
        self.set_enable_and_enable_orgs_and_disable_orgs(module_config)

        feedback_prompt_config = (
            module_config.get(SUBMODULE_FEEDBACK_PROMPT, {}) if module_config else {}
        )
        self.modal.set_enable_and_enable_orgs_and_disable_orgs(
            feedback_prompt_config.get(FEATURE_MODAL)
        )


class ResourceCommentConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__(MODULE_RESOURCES)
        self.default = True

        parents = self.conf_path + [SUBMODULE_COMMENTS]
        # TODO:Standardize to either repeated_post_limit or　repeat_post_limit
        self.repeat_post_limit = BaseConfig('repeated_post_limit', parents)
        self.repeat_post_limit.default = False

        self.rating = BaseConfig(FEATURE_RATING, parents)
        self.rating.default = False

        self.image_attachment = BaseConfig(FEATURE_IMAGE_ATTACHMENT, parents)
        self.image_attachment.default = False

        self.reply_open = BaseConfig(
            FEATURE_REPLY_OPEN, self.conf_path + [SUBMODULE_COMMENTS]
        )
        self.reply_open.default = False

    def load_config(self, feedback_config):
        module_config = feedback_config.get(FB_CONF_KEY_MODULES, {}).get(
            MODULE_RESOURCES
        )
        self.set_enable_and_enable_orgs_and_disable_orgs(module_config)
        # submodule setting
        comments_config = (
            module_config.get(SUBMODULE_COMMENTS, {}) if module_config else {}
        )

        self.repeat_post_limit.set_enable_and_enable_orgs_and_disable_orgs(
            comments_config.get(FEATURE_REPEAT_POST_LIMIT)
        )
        self.rating.set_enable_and_enable_orgs_and_disable_orgs(
            comments_config.get(FEATURE_RATING)
        )
        self.image_attachment.set_enable_and_enable_orgs_and_disable_orgs(
            comments_config.get(FEATURE_IMAGE_ATTACHMENT)
        )
        self.reply_open.set_enable_and_enable_orgs_and_disable_orgs(
            comments_config.get(FEATURE_REPLY_OPEN)
        )


class UtilizationConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__(MODULE_UTILIZATIONS)
        self.default = True

    def load_config(self, feedback_config):
        module_config = feedback_config.get(FB_CONF_KEY_MODULES, {}).get(
            MODULE_UTILIZATIONS
        )
        self.set_enable_and_enable_orgs_and_disable_orgs(module_config)


class UtilizationCommentConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__(MODULE_UTILIZATIONS)
        self.default = True
        parents = self.conf_path + [SUBMODULE_COMMENTS]
        self.image_attachment = BaseConfig(FEATURE_IMAGE_ATTACHMENT, parents)
        self.image_attachment.default = False

        self.reply_open = BaseConfig(FEATURE_REPLY_OPEN, parents)
        self.reply_open.default = False

    def load_config(self, feedback_config):
        module_config = feedback_config.get(FB_CONF_KEY_MODULES, {}).get(
            MODULE_UTILIZATIONS
        )
        self.set_enable_and_enable_orgs_and_disable_orgs(module_config)

        comments_config = (
            module_config.get(SUBMODULE_COMMENTS, {}) if module_config else {}
        )
        self.image_attachment.set_enable_and_enable_orgs_and_disable_orgs(
            comments_config.get(FEATURE_IMAGE_ATTACHMENT)
        )
        self.reply_open.set_enable_and_enable_orgs_and_disable_orgs(
            comments_config.get(FEATURE_REPLY_OPEN)
        )


class LikesConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__(MODULE_LIKES)
        self.default = True

    def load_config(self, feedback_config):
        module_config = feedback_config.get(FB_CONF_KEY_MODULES, {}).get(MODULE_LIKES)
        self.set_enable_and_enable_orgs_and_disable_orgs(module_config)


class ReCaptchaConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__(MODULE_RECAPTCHA)
        self.default = False

        parents = self.conf_path
        self.privatekey = BaseConfig('privatekey', parents)
        self.privatekey.default = ''
        self.publickey = BaseConfig('publickey', parents)
        self.publickey.default = ''
        self.score_threshold = BaseConfig('score_threshold', parents)
        self.score_threshold.default = 0.5
        self.force_all = BaseConfig('force_all', parents)
        self.force_all.default = False

    def load_config(self, feedback_config):
        self.set_config(
            feedback_config=feedback_config,
            fb_conf_path=self.conf_path + [FIELD_ENABLE],
            ckan_conf_path=self.conf_path + [FIELD_ENABLE],
        )

        self.privatekey.set_config(feedback_config)
        self.publickey.set_config(feedback_config)
        self.score_threshold.set_config(feedback_config)
        self.force_all.set_config(feedback_config)


class NoticeEmailConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__('email', [MODULE_NOTICE])
        self.default = False

        parents = self.conf_path
        self.template_directory = BaseConfig('template_directory', parents)
        # e.g., /usr/lib/python3.10/site-packages
        # /ckanext/feedback/templates/email_notification
        email_template_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), '..', '..', 'templates', 'email_notification'
            )
        )
        self.template_directory.default = email_template_dir
        self.template_utilization = BaseConfig('template_utilization', parents)
        self.template_utilization.default = 'utilization.text'

        self.template_utilization_comment = BaseConfig(
            'template_utilization_comment', parents
        )
        self.template_utilization_comment.default = 'utilization_comment.text'

        self.template_resource_comment = BaseConfig(
            'template_resource_comment', parents
        )
        self.template_resource_comment.default = 'resource_comment.text'

        self.subject_utilization = BaseConfig('subject_utilization', parents)
        self.subject_utilization.default = 'Post a Utilization'

        self.subject_utilization_comment = BaseConfig(
            'subject_utilization_comment', parents
        )
        self.subject_utilization_comment.default = 'Post a Utilization comment'

        self.subject_resource_comment = BaseConfig('subject_resource_comment', parents)
        self.subject_resource_comment.default = 'Post a Resource comment'

    def load_config(self, feedback_config):
        self.set_config(
            feedback_config=feedback_config,
            fb_conf_path=self.conf_path + [FIELD_ENABLE],
            ckan_conf_path=self.conf_path + [FIELD_ENABLE],
        )

        self.template_directory.set_config(feedback_config=feedback_config)
        self.template_utilization.set_config(feedback_config)
        self.template_utilization_comment.set_config(feedback_config=feedback_config)
        self.template_resource_comment.set_config(feedback_config=feedback_config)
        self.subject_utilization.set_config(feedback_config)
        self.subject_utilization_comment.set_config(feedback_config=feedback_config)
        self.subject_resource_comment.set_config(feedback_config)


class MoralKeeperAiConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__(MODULE_MORAL_KEEPER_AI)
        self.default = False

    def load_config(self, feedback_config):
        module_config = feedback_config.get(FB_CONF_KEY_MODULES, {}).get(
            MODULE_MORAL_KEEPER_AI
        )
        self.set_enable_and_enable_orgs_and_disable_orgs(module_config)


class FeedbackConfig(Singleton):
    is_feedback_config_file = None
    _initialized = False

    def __init__(self):
        if not self.__class__._initialized:
            self.__class__._initialized = True
            self.config_default_dir = '/srv/app'
            self.config_file_name = 'feedback_config.json'
            self.feedback_config_path = config.get(
                'ckan.feedback.config_file', self.config_default_dir
            )
            self.is_feedback_config_file = False
            self.download = DownloadsConfig()
            self.resource_comment = ResourceCommentConfig()
            self.utilization = UtilizationConfig()
            self.utilization_comment = UtilizationCommentConfig()
            self.recaptcha = ReCaptchaConfig()
            self.notice_email = NoticeEmailConfig()
            self.like = LikesConfig()
            self.moral_keeper_ai = MoralKeeperAiConfig()

    def load_feedback_config(self):
        try:
            with open(
                f'{self.feedback_config_path}/feedback_config.json', 'r'
            ) as json_file:
                self.is_feedback_config_file = True
                feedback_config = json.load(json_file)
                validate_feedback_config(feedback_config)
                for value in self.__dict__.values():
                    if isinstance(value, BaseConfig):
                        value.load_config(feedback_config)

        except FileNotFoundError:
            toolkit.error_shout(
                'The feedback config file not found. '
                f'{self.feedback_config_path}/feedback_config.json'
            )
            self.is_feedback_config_file = False
        except json.JSONDecodeError as e:
            toolkit.error_shout(
                f'The feedback config file not decoded correctly: {e.msg} '
                f'(line {e.lineno}, column {e.colno})'
            )
            raise e
        except toolkit.ValidationError as e:
            error_message = e.__dict__.get('error_dict', {}).get('message', '')
            toolkit.error_shout(
                f'The feedback config file validation failed: {error_message}'
            )
            raise e
