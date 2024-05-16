import logging

from ckan.model.group import Group
from ckan.plugins import toolkit
from werkzeug.utils import import_string

from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)

CONFIG_HANDLER_PATH = 'ckan.feedback.download_handler'


def get_organization(org_id=None):
    return session.query(Group.name.label('name')).filter(Group.id == org_id).first()


def download_handler():
    handler_path = toolkit.config.get(CONFIG_HANDLER_PATH)
    if handler_path:
        handler = import_string(handler_path, silent=True)
    else:
        handler = None
        log.warning(f'Missing {CONFIG_HANDLER_PATH} config option.')

    return handler
