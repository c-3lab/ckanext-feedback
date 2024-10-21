import json
import logging
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


class Singleton(object):
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self.__class__._initialized:
            self.__class__._initialized = True
            return True
        else:
            return False


class feedbackConfigInterface(ABC):
    @abstractmethod
    def load_config(self, feedback_config):
        pass


class BaseConfig:
    def __init__(self, name: str, parent: list = []):
        self.default = None
        self.name = name
        self.ckan_conf_prefix = ['ckan', 'feedback']
        self.fb_conf_prefix = ['modules']
        self.conf_path = parent + [name]

    def get_ckan_conf_str(self):
        return '.'.join(self.ckan_conf_prefix + self.conf_path)

    def set_enable_and_enable_orgs(
        self, feedback_config: dict, default, fb_conf_path: list = []
    ):
        self.default = default
        if not fb_conf_path:
            fb_conf_path = self.conf_path

        conf_tree = feedback_config
        try:
            for key in self.fb_conf_prefix + fb_conf_path:
                conf_tree = conf_tree.get(key)

            ckan_conf_str = self.get_ckan_conf_str()
            config[f"{ckan_conf_str}.enable"] = conf_tree.get("enable")
            config[f"{ckan_conf_str}.enable_orgs"] = conf_tree.get("enable_orgs")
        except AttributeError as e:
            toolkit.error_shout(
                f"{e}.  module[{self.name}]\nfeedback_config:{feedback_config}"
                f" feedback_conf_path:{self.fb_conf_prefix + fb_conf_path} "
                "target-key:'{key}'"
            )

    def set_config(
        self,
        feedback_config: dict,
        default,
        ckan_conf_path: list = [],
        fb_conf_path: list = [],
    ):
        self.default = default
        if not ckan_conf_path:
            ckan_conf_path = self.conf_path
        if not fb_conf_path:
            fb_conf_path = self.conf_path

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
        config[ckan_conf_path_str] = value

    def get(self):
        ck_conf_str = self.get_ckan_conf_str()
        return config.get(f"{ck_conf_str}", self.default)

    def is_enable(self, org_id=''):
        ck_conf_str = self.get_ckan_conf_str()
        enable = config.get(f"{ck_conf_str}.enable", self.default)
        if enable and FeedbackConfig().is_feedback_config_file and org_id:
            organization = get_organization(org_id)
            if organization is not None:
                enable = organization.name in config.get(
                    f"{ck_conf_str}.enable_orgs", []
                )
            else:
                enable = False
        return toolkit.asbool(enable)


class downloadsConfig(BaseConfig, feedbackConfigInterface):
    def __init__(self):
        super().__init__('downloads')

    def load_config(self, feedback_config):
        self.set_enable_and_enable_orgs(feedback_config, True)


class resourceCommentConfig(BaseConfig, feedbackConfigInterface):
    def __init__(self):
        super().__init__('resources')
        pearents = self.conf_path + ['comment']
        self.repeat_post_limit = BaseConfig('repeat_post_limit', pearents)
        self.rating = BaseConfig('rating', pearents)

    def load_config(self, feedback_config):
        self.set_enable_and_enable_orgs(feedback_config, True)

        fb_comments_conf_path = self.conf_path + ['comments']
        self.repeat_post_limit.set_enable_and_enable_orgs(
            feedback_config=feedback_config,
            fb_conf_path=fb_comments_conf_path + [self.repeat_post_limit.name],
            default=False,
        )

        self.rating.set_enable_and_enable_orgs(
            feedback_config=feedback_config,
            fb_conf_path=fb_comments_conf_path + [self.rating.name],
            default=False,
        )


class utilizationConfig(BaseConfig, feedbackConfigInterface):
    def __init__(self):
        super().__init__('utilizations')

    def load_config(self, feedback_config):
        self.set_enable_and_enable_orgs(feedback_config, True)


class reCaptchaConfig(BaseConfig, feedbackConfigInterface):
    def __init__(self):
        super().__init__('recaptcha')

        parents = self.conf_path
        self.privatekey = BaseConfig('privatekey', parents)
        self.publickey = BaseConfig('publickey', parents)
        self.score_threshold = BaseConfig('score_threshold', parents)

    def load_config(self, feedback_config):
        self.set_config(
            feedback_config=feedback_config,
            fb_conf_path=self.conf_path + ['enable'],
            ckan_conf_path=self.conf_path + ['enable'],
            default=False,
        )

        self.privatekey.set_config(feedback_config, default='')
        self.publickey.set_config(feedback_config, default='')
        self.score_threshold.set_config(feedback_config, default=0.5)


class noticeEmailConfig(BaseConfig, feedbackConfigInterface):
    def __init__(self):
        super().__init__('email', ['notice'])

        parents = self.conf_path
        self.template_directory = BaseConfig('template_directory', parents)
        self.template_utilization = BaseConfig('template_utilization', parents)
        self.template_utilization_comment = BaseConfig(
            'template_utilization_comment', parents
        )
        self.template_resource_comment = BaseConfig(
            'template_resource_comment', parents
        )
        self.subject_utilization = BaseConfig('subject_utilization', parents)
        self.subject_utilization_comment = BaseConfig(
            'subject_utilization_comment', parents
        )
        self.subject_resource_comment = BaseConfig('subject_resource_comment', parents)

    def load_config(self, feedback_config):
        self.set_config(
            feedback_config=feedback_config,
            fb_conf_path=self.conf_path + ['enable'],
            ckan_conf_path=self.conf_path + ['enable'],
            default=False,
        )

        self.template_directory.set_config(
            feedback_config=feedback_config,
            default='/srv/app/src_extensions/ckanext-feedback/'
            'ckanext/feedback/templates/email_notificatio',
        )
        self.template_utilization.set_config(feedback_config, 'utilization.text')
        self.template_utilization_comment.set_config(
            feedback_config=feedback_config, default='utilization_comment.text'
        )
        self.template_resource_comment.set_config(
            feedback_config=feedback_config, default='resource_comment.text'
        )
        self.subject_utilization.set_config(feedback_config, 'Post a Utilization')
        self.subject_utilization_comment.set_config(
            feedback_config=feedback_config, default='Post a Utilization comment'
        )
        self.subject_resource_comment.set_config(
            feedback_config, 'Post a Resource comment'
        )


class FeedbackConfig(Singleton):
    is_feedback_config_file = None

    def __init__(self):
        if super().__init__():
            self.config_default_dir = '/srv/app'
            self.config_file_name = 'feedback_config.json'
            self.feedback_config_path = config.get(
                'ckan.feedback.config_file', self.config_default_dir
            )
            self.is_feedback_config_file = False

            self.download = downloadsConfig()
            self.resource_comment = resourceCommentConfig()
            self.utilization = utilizationConfig()
            self.recaptcha = reCaptchaConfig()
            self.notice_email = noticeEmailConfig()

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
            toolkit.error_shout('The feedback config file not found')
            self.is_feedback_config_file = False
        except json.JSONDecodeError:
            toolkit.error_shout('The feedback config file not decoded correctly')
