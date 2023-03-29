from unittest.mock import patch

import pytest
from ckan import model
from click.testing import CliRunner

from ckanext.feedback.command.feedback import feedback, get_engine

from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.models.issue import IssueResolution, IssueResolutionSummary
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentReply,
    ResourceCommentSummary,
)
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationSummary,
)

engine = get_engine('db', '5432', 'ckan_test', 'ckan', 'ckan')


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestFeedbackCommand:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()

    def setup_method(self, method):
        self.runner = CliRunner()

    def test_feedback_default(self):
        result = self.runner.invoke(feedback, ['init'])
        assert 'Initialize all modules: SUCCESS' in result.output
        assert engine.has_table(Utilization.__table__)
        assert engine.has_table(Utilization.__table__)
        assert engine.has_table(UtilizationComment.__table__)
        assert engine.has_table(UtilizationSummary.__table__)
        assert engine.has_table(IssueResolution.__table__)
        assert engine.has_table(IssueResolutionSummary.__table__)
        assert engine.has_table(ResourceComment.__table__)
        assert engine.has_table(ResourceCommentReply.__table__)
        assert engine.has_table(ResourceCommentSummary.__table__)
        assert engine.has_table(DownloadSummary.__table__)

    def test_feedback_utilization(self):
        result = self.runner.invoke(feedback, ['init', '--modules', 'utilization', '--dbname', 'ckan_test'])
        assert 'Initialize utilization: SUCCESS' in result.output
        assert engine.has_table(Utilization.__table__)
        assert engine.has_table(UtilizationComment.__table__)
        assert engine.has_table(UtilizationSummary.__table__)
        assert engine.has_table(IssueResolution.__table__)
        assert engine.has_table(IssueResolutionSummary.__table__)

    def test_feedback_resource(self):
        result = self.runner.invoke(feedback, ['init', '--modules', 'resource', '--dbname', 'ckan_test'])
        assert 'Initialize resource: SUCCESS' in result.output
        assert engine.has_table(ResourceComment.__table__)
        assert engine.has_table(ResourceCommentReply.__table__)
        assert engine.has_table(ResourceCommentSummary.__table__)

    def test_feedback_download(self):
        result = self.runner.invoke(feedback, ['init', '--modules', 'download', '--dbname', 'ckan_test'])
        assert 'Initialize download: SUCCESS' in result.output
        assert engine.has_table(DownloadSummary.__table__)

    def test_feedback_with_db_option(self):
        result = self.runner.invoke(
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
        assert 'Initialize all modules: SUCCESS' in result.output
        assert engine.has_table(Utilization.__table__)
        assert engine.has_table(Utilization.__table__)
        assert engine.has_table(UtilizationComment.__table__)
        assert engine.has_table(UtilizationSummary.__table__)
        assert engine.has_table(IssueResolution.__table__)
        assert engine.has_table(IssueResolutionSummary.__table__)
        assert engine.has_table(ResourceComment.__table__)
        assert engine.has_table(ResourceCommentReply.__table__)
        assert engine.has_table(ResourceCommentSummary.__table__)
        assert engine.has_table(DownloadSummary.__table__)

    def test_feedback_engine_error(self):
        with patch(
            'ckanext.feedback.command.feedback.create_engine',
            side_effect=Exception('Error message'),
        ):
            result = self.runner.invoke(feedback, ['init'])

        assert result.exit_code != 0

    def test_feedback_session_error(self):
        with patch(
            'ckanext.feedback.command.feedback.create_utilization_tables',
            side_effect=Exception('Error message'),
        ):
            result = self.runner.invoke(feedback, ['init'])

        assert result.exit_code != 0
