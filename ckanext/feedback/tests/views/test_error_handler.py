from unittest.mock import patch

import pytest
from ckan import model
from flask import Blueprint, Flask
from psycopg2.errors import UndefinedTable
from sqlalchemy.exc import ProgrammingError

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.views.error_handler import add_error_handler

engine = model.repo.session.get_bind()


def dummy_func_with_undefined_table(**kwargs):
    raise ProgrammingError(statement='', params='', orig=UndefinedTable('', '', ''))


def dummy_func_with_programming_error(**kwargs):
    raise ProgrammingError(statement='', params='', orig=None)


def dummy_func_with_exception(**kwargs):
    raise Exception()


@add_error_handler
def function():
    blueprint = Blueprint(
        'test',
        __name__,
        url_prefix='/',
    )
    blueprint.add_url_rule(
        '/test_undefined_table',
        view_func=dummy_func_with_undefined_table,
    )
    blueprint.add_url_rule(
        '/test_programming_error',
        view_func=dummy_func_with_programming_error,
    )
    blueprint.add_url_rule('/test_exception', view_func=dummy_func_with_exception)
    return blueprint


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestErrorHandler:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.register_blueprint(function())

    @patch('ckanext.feedback.views.error_handler.session', autospec=True)
    @patch('ckanext.feedback.views.error_handler.log', autospec=True)
    def test_handle_programming_error_with_undefined_table(
        self, mock_log, mock_session
    ):
        with self.app.test_client() as client:
            with pytest.raises(ProgrammingError):
                client.get('/test_undefined_table')
            mock_log.error.assert_called_once()
            mock_session.rollback.assert_called_once()

    @patch('ckanext.feedback.views.error_handler.session', autospec=True)
    def test_handle_programming_error(self, mock_session):
        with self.app.test_client() as client:
            with pytest.raises(ProgrammingError):
                client.get('/test_programming_error')
            mock_session.rollback.assert_called_once()

    @patch('ckanext.feedback.views.error_handler.session', autospec=True)
    def test_handle_exception(self, mock_session):
        with self.app.test_client() as client:
            with pytest.raises(Exception):
                client.get('/test_exception')
            mock_session.rollback.assert_called_once()
