import pytest
from unittest.mock import patch
from sqlalchemy.exc import ProgrammingError
from psycopg2.errors import UndefinedTable
from ckanext.feedback.views.error_handler import add_error_handler

from unittest.mock import patch

import pytest
import six
from ckan import model
from ckan.model import User
from ckan.tests import factories
from flask import Flask, g, Blueprint


engine = model.repo.session.get_bind()

blueprint = Blueprint(
        'test',
        __name__,
        url_prefix='/example',
        url_defaults={'package_type': 'dataset'},
    )


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestErrorHandler:
    @patch('ckanext.feedback.views.error_handler.session', autospec=True)
    @patch('ckanext.feedback.views.error_handler.log', autospec=True)
    def test_handle_programming_error_with_undefined_table(self, mock_log, mock_session):

        def dummy_func(**kwargs):
            raise ProgrammingError(statement="", params="", orig=UndefinedTable("", "", ""))

        def another_dummy_func(**kwargs):
            raise Exception()

        def the_other_dummy_func(**kwargs):
            raise ProgrammingError(statement="", params="", orig=None)

        @add_error_handler
        def function():
            blueprint = Blueprint(
                'test',
                __name__,
                url_prefix='/example',
                url_defaults={'package_type': 'dataset'},
            )
            blueprint.add_url_rule(
                '/test_handle_programming_error_with_undefined_table', view_func=dummy_func
            )
            blueprint.add_url_rule(
                '/test_handle_exception', view_func=another_dummy_func
            )
            blueprint.add_url_rule(
                '/test_handle_programming_error_without_undefined_table', view_func=the_other_dummy_func
            )
            return blueprint

        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(function())

        with app.test_client() as client:
            with pytest.raises(ProgrammingError):
                client.get('/example/test_handle_programming_error_with_undefined_table')
            mock_log.error.assert_called_once()
            mock_session.rollback.assert_called_once()
            
            mock_log.reset_mock()
            mock_session.reset_mock()

            with pytest.raises(Exception):
                client.get('/example/test_handle_exception')
            mock_session.rollback.assert_called_once()

            mock_session.reset_mock()

            with pytest.raises(ProgrammingError):
                client.get('/example/test_handle_programming_error_without_undefined_table')
            mock_session.rollback.assert_called_once()
