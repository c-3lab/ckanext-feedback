import logging

from psycopg2.errors import UndefinedTable
from sqlalchemy.exc import ProgrammingError

from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)

_registered_blueprints = set()


def add_error_handler(func):
    def wrapper():
        blueprint = func()

        if blueprint.name in _registered_blueprints:
            return blueprint

        _registered_blueprints.add(blueprint.name)

        @blueprint.errorhandler(ProgrammingError)
        def handle_programming_error(e):
            if isinstance(e.orig, UndefinedTable):
                log.error(
                    'Some tables does not exit.'
                    ' Run "ckan --config=/etc/ckan/production.ini feedback init".'
                )

            session.rollback()
            raise e

        @blueprint.errorhandler(Exception)
        def handle_exception(e):
            session.rollback()
            raise e

        return blueprint

    return wrapper
