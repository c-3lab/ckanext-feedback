from unittest.mock import patch

import pytest
from ckan import model
from click.testing import CliRunner

from ckanext.feedback.command.feedback import feedback


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestFeedbackCommand:
    model.repo.init_db()

    def test_feedback_default(self):
        runner = CliRunner()
        first_result = runner.invoke(feedback, ['init'])
        assert 'Initialize all modules: SUCCESS' in first_result.output
        second_result = runner.invoke(feedback, ['init'])
        assert 'Initialize all modules: SUCCESS' in second_result.output

    def test_feedback_utilization_option(self):
        runner = CliRunner()
        first_result = runner.invoke(feedback, ['init', '--modules', 'utilization'])
        assert 'Initialize utilization: SUCCESS' in first_result.output
        second_result = runner.invoke(feedback, ['init', '--modules', 'utilization'])
        assert 'Initialize utilization: SUCCESS' in second_result.output

    def test_feedback_resource_option(self):
        runner = CliRunner()
        first_result = runner.invoke(feedback, ['init', '--modules', 'resource'])
        assert 'Initialize resource: SUCCESS' in first_result.output
        second_result = runner.invoke(feedback, ['init', '--modules', 'resource'])
        assert 'Initialize resource: SUCCESS' in second_result.output

    def test_feedback_download_option(self):
        runner = CliRunner()
        first_result = runner.invoke(feedback, ['init', '--modules', 'download'])
        assert 'Initialize download: SUCCESS' in first_result.output
        second_result = runner.invoke(feedback, ['init', '--modules', 'download'])
        assert 'Initialize download: SUCCESS' in second_result.output

    def test_feedback_with_db_option(self):
        runner = CliRunner()
        first_result = runner.invoke(
            feedback,
            [
                'init',
                '--host',
                'db',
                '--port',
                5432,
                '--dbname',
                'ckan',
                '--user',
                'ckan',
                '--password',
                'ckan',
            ],
        )
        assert 'Initialize all modules: SUCCESS' in first_result.output
        second_result = runner.invoke(
            feedback,
            [
                'init',
                '--host',
                'db',
                '--port',
                5432,
                '--dbname',
                'ckan',
                '--user',
                'ckan',
                '--password',
                'ckan',
            ],
        )
        assert 'Initialize all modules: SUCCESS' in second_result.output

    def test_feedback_error(self):
        runner = CliRunner()

        def mock_function(*args, **kwargs):
            raise Exception('Error message')

        with patch(
            'ckanext.feedback.command.feedback.create_utilization_tables',
            side_effect=mock_function,
        ):
            result = runner.invoke(feedback, ['init'])

        assert result.exit_code != 0
