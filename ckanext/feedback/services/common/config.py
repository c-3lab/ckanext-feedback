import json
import logging
import os
from abc import ABC, abstractmethod

from ckan.common import config
from ckan.model.group import Group
from ckan.plugins import toolkit
from werkzeug.utils import import_string

from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)

CONFIG_HANDLER_PATH = 'ckan.feedback.download_handler'


def get_organization(org_id=None):
    return session.query(Group.name.label('name')).filter(Group.id == org_id).first()


def download_handler():
    handler_path = config.get(CONFIG_HANDLER_PATH)
    if handler_path:
        handler = import_string(handler_path, silent=True)
    else:
        handler = None
        log.warning(f'Missing {CONFIG_HANDLER_PATH} config option.')

    return handler


def is_list_of_str(value):
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


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
        self.fb_conf_prefix = ['modules']
        self.conf_path = (parent or []) + [name]

    def get_ckan_conf_str(self):
        return '.'.join(self.ckan_conf_prefix + self.conf_path)

    def set_enable_and_enable_orgs_and_disable_orgs(
        self, feedback_config: dict, fb_conf_path: list = None
    ):
        fb_conf_path = fb_conf_path or self.conf_path
        key_list = self.fb_conf_prefix + fb_conf_path

        conf_tree = feedback_config

        ckan_conf_str = self.get_ckan_conf_str()

        for key in key_list:
            conf_tree = conf_tree.get(key)

            if conf_tree is None:
                config.pop(f"{ckan_conf_str}.enable", None)
                return

            if key == key_list[-1]:
                enable = conf_tree.get("enable")
                if enable is None:
                    message = (
                        f"The configuration of the \"{key}\" module "
                        "in \"feedback_config.json\" is incomplete. "
                        "Please specify the \"enable\" key "
                        f"(e.g., {{\"modules\": {{\"{key}\": {{\"enable\": true}}}}}})."
                    )
                    raise toolkit.ValidationError({"message": message})
                enable_orgs = conf_tree.get("enable_orgs")
                disable_orgs = conf_tree.get("disable_orgs")

        config[f"{ckan_conf_str}.enable"] = enable
        if enable_orgs:
            config[f"{ckan_conf_str}.enable_orgs"] = enable_orgs
        if disable_orgs:
            config[f"{ckan_conf_str}.disable_orgs"] = disable_orgs

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
                log.debug(
                    f"module[{self.name}]\nfeedback_config:{feedback_config}"
                    f" feedback_conf_path:{self.fb_conf_prefix + fb_conf_path} "
                    "target-key:'{key}'"
                )
        if value is not None:
            config[ckan_conf_path_str] = value

    def get(self):
        ck_conf_str = self.get_ckan_conf_str()
        return config.get(f"{ck_conf_str}", self.default)

    def is_enable(self, org_id=''):
        ck_conf_str = self.get_ckan_conf_str()
        # Retrieve the on/off value for the feature from the ini file
        enable = config.get(f"{ck_conf_str}.enable", self.default)

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
        organization = get_organization(org_id)

        # Return False if the specified organization cannot be retrieved
        if not organization:
            return False

        # Retrieve the list of enabled organizations and disabled
        # organizations from the ini file
        enable_orgs = config.get(f"{ck_conf_str}.enable_orgs")
        disable_orgs = config.get(f"{ck_conf_str}.disable_orgs")

        # Return True if neither the list of enabled organizations
        # nor the list of disabled organizations exists
        if not enable_orgs and not disable_orgs:
            return enable

        # Raise a ValidationError if the list of enabled
        # organizations exists and is not an array of strings
        if enable_orgs and not is_list_of_str(enable_orgs):
            raise toolkit.ValidationError(
                {
                    "message": (
                        "The \"enable_orgs\" key must be a string array "
                        "to specify valid organizations "
                        "(e.g., \"enable_orgs\": [\"org-name-a\", \"org-name-b\"])."
                    )
                }
            )

        # Raise a ValidationError if the list of disabled
        # organizations exists and is not an array of strings
        if disable_orgs and not is_list_of_str(disable_orgs):
            raise toolkit.ValidationError(
                {
                    "message": (
                        "The \"disable_orgs\" key must be a string array "
                        "to specify invalid organizations "
                        "(e.g., \"disable_orgs\": [\"org-name-a\", \"org-name-b\"])."
                    )
                }
            )

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

    def get_enable_orgs(self):
        ck_conf_str = self.get_ckan_conf_str()
        enable = config.get(f"{ck_conf_str}.enable", self.default)
        if enable:
            return config.get(f"{ck_conf_str}.enable_orgs", [])
        return enable


class DownloadsConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__('downloads')
        self.default = True

    def load_config(self, feedback_config):
        self.set_enable_and_enable_orgs_and_disable_orgs(feedback_config)


class ResourceCommentConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__('resources')
        self.default = True

        parents = self.conf_path + ['comment']
        # TODO:Standardize to either repeated_post_limit or　repeat_post_limit
        self.repeat_post_limit = BaseConfig('repeated_post_limit', parents)
        self.repeat_post_limit.default = False

        self.rating = BaseConfig('rating', parents)
        self.rating.default = False

    def load_config(self, feedback_config):
        self.set_enable_and_enable_orgs_and_disable_orgs(feedback_config)

        fb_comments_conf_path = self.conf_path + ['comments']
        self.repeat_post_limit.set_enable_and_enable_orgs_and_disable_orgs(
            feedback_config=feedback_config,
            fb_conf_path=fb_comments_conf_path + ['repeat_post_limit'],
        )

        self.rating.set_enable_and_enable_orgs_and_disable_orgs(
            feedback_config=feedback_config,
            fb_conf_path=fb_comments_conf_path + [self.rating.name],
        )


class UtilizationConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__('utilizations')
        self.default = True

    def load_config(self, feedback_config):
        self.set_enable_and_enable_orgs_and_disable_orgs(feedback_config)


class LikesConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__('likes')
        self.default = True

    def load_config(self, feedback_config):
        self.set_enable_and_enable_orgs_and_disable_orgs(feedback_config)


class ReCaptchaConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__('recaptcha')
        self.default = False

        parents = self.conf_path
        self.privatekey = BaseConfig('privatekey', parents)
        self.privatekey.default = ''
        self.publickey = BaseConfig('publickey', parents)
        self.publickey.default = ''
        self.score_threshold = BaseConfig('score_threshold', parents)
        self.score_threshold.default = 0.5

    def load_config(self, feedback_config):
        self.set_config(
            feedback_config=feedback_config,
            fb_conf_path=self.conf_path + ['enable'],
            ckan_conf_path=self.conf_path + ['enable'],
        )

        self.privatekey.set_config(feedback_config)
        self.publickey.set_config(feedback_config)
        self.score_threshold.set_config(feedback_config)


class NoticeEmailConfig(BaseConfig, FeedbackConfigInterface):
    def __init__(self):
        super().__init__('email', ['notice'])
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
            fb_conf_path=self.conf_path + ['enable'],
            ckan_conf_path=self.conf_path + ['enable'],
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
        super().__init__('moral_keeper_ai')
        self.default = False

    def load_config(self, feedback_config):
        self.set_enable_and_enable_orgs_and_disable_orgs(feedback_config)


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
                for value in self.__dict__.values():
                    if isinstance(value, BaseConfig):
                        value.load_config(feedback_config)
        except FileNotFoundError:
            toolkit.error_shout(
                'The feedback config file not found. '
                f'{self.feedback_config_path}/feedback_config.json'
            )
            self.is_feedback_config_file = False
        except json.JSONDecodeError:
            toolkit.error_shout('The feedback config file not decoded correctly')
