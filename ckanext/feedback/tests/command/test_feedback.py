from unittest.mock import patch

import pytest
from ckan import model
from click.testing import CliRunner

from ckanext.feedback.command.feedback import feedback
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

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestFeedbackCommand:
    @classmethod
    def setup_class(cls):
        model.repo.metadata.clear()
        model.repo.init_db()

    def teardown_class(cls):
        model.repo.metadata.reflect()

    def setup_method(self, method):
        self.runner = CliRunner()

    def teardown_method(self, method):
        model.repo.metadata.drop_all(
            engine,
            [
                Utilization.__table__,
                UtilizationComment.__table__,
                UtilizationSummary.__table__,
                IssueResolution.__table__,
                IssueResolutionSummary.__table__,
                ResourceComment.__table__,
                ResourceCommentReply.__table__,
                ResourceCommentSummary.__table__,
                DownloadSummary.__table__,
            ],
            checkfirst=True,
        )

    def test_feedback_default(self):
        result = self.runner.invoke(feedback, ['init', '--dbname', engine.url.database])
        assert 'Initialize all modules: SUCCESS' in result.output
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
        result = self.runner.invoke(
            feedback,
            ['init', '--modules', 'utilization', '--dbname', engine.url.database],
        )
        assert 'Initialize utilization: SUCCESS' in result.output
        assert engine.has_table(Utilization.__table__)
        assert engine.has_table(UtilizationComment.__table__)
        assert engine.has_table(UtilizationSummary.__table__)
        assert engine.has_table(IssueResolution.__table__)
        assert engine.has_table(IssueResolutionSummary.__table__)
        assert not engine.has_table(ResourceComment.__table__)
        assert not engine.has_table(ResourceCommentReply.__table__)
        assert not engine.has_table(ResourceCommentSummary.__table__)
        assert not engine.has_table(DownloadSummary.__table__)

    def test_feedback_resource(self):
        result = self.runner.invoke(
            feedback, ['init', '--modules', 'resource', '--dbname', engine.url.database]
        )
        assert 'Initialize resource: SUCCESS' in result.output
        assert not engine.has_table(Utilization.__table__)
        assert not engine.has_table(UtilizationComment.__table__)
        assert not engine.has_table(UtilizationSummary.__table__)
        assert not engine.has_table(IssueResolution.__table__)
        assert not engine.has_table(IssueResolutionSummary.__table__)
        assert engine.has_table(ResourceComment.__table__)
        assert engine.has_table(ResourceCommentReply.__table__)
        assert engine.has_table(ResourceCommentSummary.__table__)
        assert not engine.has_table(DownloadSummary.__table__)

    def test_feedback_download(self):
        result = self.runner.invoke(
            feedback, ['init', '--modules', 'download', '--dbname', engine.url.database]
        )
        assert 'Initialize download: SUCCESS' in result.output
        assert not engine.has_table(Utilization.__table__)
        assert not engine.has_table(UtilizationComment.__table__)
        assert not engine.has_table(UtilizationSummary.__table__)
        assert not engine.has_table(IssueResolution.__table__)
        assert not engine.has_table(IssueResolutionSummary.__table__)
        assert not engine.has_table(ResourceComment.__table__)
        assert not engine.has_table(ResourceCommentReply.__table__)
        assert not engine.has_table(ResourceCommentSummary.__table__)
        assert engine.has_table(DownloadSummary.__table__)

    def test_feedback_with_db_option(self):
        result = self.runner.invoke(
            feedback,
            [
                'init',
                '--host',
                engine.url.host,
                '--port',
                engine.url.port,
                '--dbname',
                engine.url.database,
                '--user',
                engine.url.username,
                '--password',
                engine.url.password,
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
            result = self.runner.invoke(
                feedback, ['init', '--dbname', engine.url.database]
            )

        assert result.exit_code != 0
        assert not engine.has_table(Utilization.__table__)
        assert not engine.has_table(UtilizationComment.__table__)
        assert not engine.has_table(UtilizationSummary.__table__)
        assert not engine.has_table(IssueResolution.__table__)
        assert not engine.has_table(IssueResolutionSummary.__table__)
        assert not engine.has_table(ResourceComment.__table__)
        assert not engine.has_table(ResourceCommentReply.__table__)
        assert not engine.has_table(ResourceCommentSummary.__table__)
        assert not engine.has_table(DownloadSummary.__table__)

    def test_feedback_session_error(self):
        with patch(
            'ckanext.feedback.command.feedback.create_utilization_tables',
            side_effect=Exception('Error message'),
        ):
            result = self.runner.invoke(
                feedback, ['init', '--dbname', engine.url.database]
            )

        assert result.exit_code != 0
        assert not engine.has_table(Utilization.__table__)
        assert not engine.has_table(UtilizationComment.__table__)
        assert not engine.has_table(UtilizationSummary.__table__)
        assert not engine.has_table(IssueResolution.__table__)
        assert not engine.has_table(IssueResolutionSummary.__table__)
        assert not engine.has_table(ResourceComment.__table__)
        assert not engine.has_table(ResourceCommentReply.__table__)
        assert not engine.has_table(ResourceCommentSummary.__table__)
        assert not engine.has_table(DownloadSummary.__table__)
