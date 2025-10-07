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

        # Note: session.close() is removed because the global session object
        # is shared across all requests and should not be closed per-request.
        # SQLAlchemy will manage connection pooling automatically.

        return blueprint

    return wrapper
