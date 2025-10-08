import logging

from psycopg2.errors import UndefinedTable
from sqlalchemy.exc import ProgrammingError

from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


def add_error_handler(func):
    def wrapper():
        blueprint = func()

        @blueprint.app_errorhandler(ProgrammingError)
        def handle_programming_error(e):
            if isinstance(e.orig, UndefinedTable):
                log.error(
                    'Some tables does not exit.'
                    ' Run "ckan --config=/etc/ckan/production.ini feedback init".'
                )

            session.rollback()
            raise e

        @blueprint.app_errorhandler(Exception)
        def handle_exception(e):
            session.rollback()
            raise e

        @blueprint.teardown_app_request
        def close_session(e=None):
            log.warning("[DEBUG] teardown_app_request called, closing session")
            log.warning(f"[DEBUG] session before close: {session}")
            log.warning(f"[DEBUG] session.is_active before: {session.is_active}")
            session.close()
            log.warning(f"[DEBUG] session.is_active after: {session.is_active}")

        return blueprint

    return wrapper
