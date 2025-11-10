from unittest.mock import MagicMock, call, patch

import pytest
from ckan import model
from click.testing import CliRunner

from ckanext.feedback.command.feedback import (
    delete_invalid_files,
    feedback,
    handle_file_deletion,
)
from ckanext.feedback.models.download import DownloadMonthly, DownloadSummary
from ckanext.feedback.models.issue import IssueResolution, IssueResolutionSummary
from ckanext.feedback.models.likes import ResourceLike, ResourceLikeMonthly
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentMoralCheckLog,
    ResourceCommentReactions,
    ResourceCommentReply,
    ResourceCommentSummary,
)
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentMoralCheckLog,
    UtilizationCommentReply,
    UtilizationSummary,
)

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestFeedbackCommand:
    @classmethod
    def setup_class(cls):
        cls._cleanup_feedback_tables()
        model.repo.metadata.clear()
        model.repo.init_db()

    @classmethod
    def teardown_class(cls):
        cls._cleanup_feedback_tables()
        model.repo.metadata.reflect()

    @classmethod
    def _cleanup_feedback_tables(cls):
        import logging

        from sqlalchemy import text
        from sqlalchemy.exc import OperationalError, ProgrammingError

        log = logging.getLogger(__name__)

        try:
            with engine.connect() as connection:
                with connection.begin():
                    feedback_tables = [
                        'utilization_comment_moral_check_log',
                        'resource_comment_moral_check_log',
                        'resource_comment_reactions',
                        'resource_comment_reply',
                        'issue_resolution',
                        'issue_resolution_summary',
                        'utilization_summary',
                        'resource_comment_summary',
                        'resource_like',
                        'resource_like_monthly',
                        'download_summary',
                        'download_monthly',
                        'utilization_comment',
                        'utilization',
                        'resource_comment',
                    ]

                    for table_name in feedback_tables:
                        try:
                            connection.execute(
                                text(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                            )
                            log.debug(f"Successfully dropped table: {table_name}")
                        except (ProgrammingError, OperationalError) as e:
                            log.debug(
                                f"Expected error dropping table {table_name}: {e}"
                            )
                        except Exception as e:
                            log.warning(
                                f"Unexpected error dropping table {table_name}: {e}"
                            )
        except Exception as e:
            log.warning(f"Failed to cleanup feedback tables: {e}")

    def setup_method(self, method):
        self.runner = CliRunner()
        model.repo.metadata.drop_all(
            engine,
            [
                IssueResolutionSummary.__table__,
                IssueResolution.__table__,
                UtilizationCommentMoralCheckLog.__table__,
                UtilizationSummary.__table__,
                UtilizationCommentReply.__table__,
                UtilizationComment.__table__,
                Utilization.__table__,
                ResourceCommentMoralCheckLog.__table__,
                ResourceCommentReactions.__table__,
                ResourceLikeMonthly.__table__,
                ResourceLike.__table__,
                ResourceCommentSummary.__table__,
                ResourceCommentReply.__table__,
                ResourceComment.__table__,
                DownloadMonthly.__table__,
                DownloadSummary.__table__,
            ],
            checkfirst=True,
        )

    def teardown_method(self, method):
        self._cleanup_feedback_tables()

    def test_feedback_default(self):
        result = self.runner.invoke(feedback, ['init'])
        assert 'Initialize all modules: SUCCESS' in result.output
        assert engine.has_table(Utilization.__table__)
        assert engine.has_table(UtilizationComment.__table__)
        assert engine.has_table(UtilizationSummary.__table__)
        assert engine.has_table(UtilizationCommentMoralCheckLog.__table__)
        assert engine.has_table(IssueResolution.__table__)
        assert engine.has_table(IssueResolutionSummary.__table__)
        assert engine.has_table(ResourceComment.__table__)
        assert engine.has_table(ResourceCommentReply.__table__)
        assert engine.has_table(ResourceCommentSummary.__table__)
        assert engine.has_table(ResourceLike.__table__)
        assert engine.has_table(ResourceLikeMonthly.__table__)
        assert engine.has_table(ResourceCommentReactions.__table__)
        assert engine.has_table(ResourceCommentMoralCheckLog.__table__)
        assert engine.has_table(DownloadSummary.__table__)
        assert engine.has_table(DownloadMonthly.__table__)

    def test_feedback_utilization(self):
        result = self.runner.invoke(
            feedback,
            ['init', '--modules', 'utilization'],
        )
        assert 'Initialize utilization: SUCCESS' in result.output
        assert engine.has_table(Utilization.__table__)
        assert engine.has_table(UtilizationComment.__table__)
        assert engine.has_table(UtilizationSummary.__table__)
        assert engine.has_table(UtilizationCommentMoralCheckLog.__table__)
        assert engine.has_table(IssueResolution.__table__)
        assert engine.has_table(IssueResolutionSummary.__table__)
        assert not engine.has_table(ResourceComment.__table__)
        assert not engine.has_table(ResourceCommentReply.__table__)
        assert not engine.has_table(ResourceCommentSummary.__table__)
        assert not engine.has_table(ResourceLike.__table__)
        assert not engine.has_table(ResourceLikeMonthly.__table__)
        assert not engine.has_table(ResourceCommentReactions.__table__)
        assert not engine.has_table(ResourceCommentMoralCheckLog.__table__)
        assert not engine.has_table(DownloadSummary.__table__)
        assert not engine.has_table(DownloadMonthly.__table__)

    def test_feedback_resource(self):
        result = self.runner.invoke(feedback, ['init', '--modules', 'resource'])
        assert 'Initialize resource: SUCCESS' in result.output
        assert not engine.has_table(Utilization.__table__)
        assert not engine.has_table(UtilizationComment.__table__)
        assert not engine.has_table(UtilizationSummary.__table__)
        assert not engine.has_table(UtilizationCommentMoralCheckLog.__table__)
        assert not engine.has_table(IssueResolution.__table__)
        assert not engine.has_table(IssueResolutionSummary.__table__)
        assert engine.has_table(ResourceComment.__table__)
        assert engine.has_table(ResourceCommentReply.__table__)
        assert engine.has_table(ResourceCommentSummary.__table__)
        assert engine.has_table(ResourceLike.__table__)
        assert engine.has_table(ResourceLikeMonthly.__table__)
        assert engine.has_table(ResourceCommentReactions.__table__)
        assert engine.has_table(ResourceCommentMoralCheckLog.__table__)
        assert not engine.has_table(DownloadSummary.__table__)
        assert not engine.has_table(DownloadMonthly.__table__)

    def test_feedback_download(self):
        result = self.runner.invoke(feedback, ['init', '--modules', 'download'])
        assert 'Initialize download: SUCCESS' in result.output
        assert not engine.has_table(Utilization.__table__)
        assert not engine.has_table(UtilizationComment.__table__)
        assert not engine.has_table(UtilizationSummary.__table__)
        assert not engine.has_table(UtilizationCommentMoralCheckLog.__table__)
        assert not engine.has_table(IssueResolution.__table__)
        assert not engine.has_table(IssueResolutionSummary.__table__)
        assert not engine.has_table(ResourceComment.__table__)
        assert not engine.has_table(ResourceCommentReply.__table__)
        assert not engine.has_table(ResourceCommentSummary.__table__)
        assert not engine.has_table(ResourceLike.__table__)
        assert not engine.has_table(ResourceLikeMonthly.__table__)
        assert not engine.has_table(ResourceCommentReactions.__table__)
        assert not engine.has_table(ResourceCommentMoralCheckLog.__table__)
        assert engine.has_table(DownloadSummary.__table__)
        assert engine.has_table(DownloadMonthly.__table__)

    def test_feedback_session_error(self):
        with patch(
            'ckanext.feedback.command.feedback.create_utilization_tables',
            side_effect=Exception('Error message'),
        ):
            result = self.runner.invoke(feedback, ['init'])

        assert result.exit_code != 0
        assert not engine.has_table(Utilization.__table__)
        assert not engine.has_table(UtilizationComment.__table__)
        assert not engine.has_table(UtilizationSummary.__table__)
        assert not engine.has_table(UtilizationCommentMoralCheckLog.__table__)
        assert not engine.has_table(IssueResolution.__table__)
        assert not engine.has_table(IssueResolutionSummary.__table__)
        assert not engine.has_table(ResourceComment.__table__)
        assert not engine.has_table(ResourceCommentReply.__table__)
        assert not engine.has_table(ResourceCommentSummary.__table__)
        assert not engine.has_table(ResourceLike.__table__)
        assert not engine.has_table(ResourceLikeMonthly.__table__)
        assert not engine.has_table(ResourceCommentReactions.__table__)
        assert not engine.has_table(ResourceCommentMoralCheckLog.__table__)
        assert not engine.has_table(DownloadSummary.__table__)
        assert not engine.has_table(DownloadMonthly.__table__)

    @patch('ckanext.feedback.command.feedback.upload_service')
    @patch('ckanext.feedback.command.feedback.comment_service')
    @patch('ckanext.feedback.command.feedback.detail_service')
    @patch('ckanext.feedback.command.feedback.os.listdir')
    @patch('ckanext.feedback.command.feedback.delete_invalid_files')
    def test_clean_files(
        self,
        mock_delete_invalid_files,
        mock_listdir,
        mock_detail_service,
        mock_comment_service,
        mock_upload_service,
    ):
        dry_run = False

        mock_upload_service.get_feedback_storage_path.return_value = '/test/upload/path'
        mock_comment_service.get_upload_destination.return_value = (
            'feedback_resource_comment'
        )
        mock_detail_service.get_upload_destination.return_value = (
            'feedback_utilization_comment'
        )
        mock_listdir.return_value = ['image1.png', 'image2.png', 'image3.png']
        mock_comment_service.get_comment_attached_image_files.return_value = [
            'image1.png',
            'image2.png',
        ]
        mock_detail_service.get_comment_attached_image_files.return_value = [
            'image1.png'
        ]
        mock_delete_invalid_files.return_value = None

        self.runner.invoke(feedback, ['clean-files'])

        mock_upload_service.get_feedback_storage_path.assert_called_once_with()
        mock_comment_service.get_upload_destination.assert_called_once_with()
        mock_detail_service.get_upload_destination.assert_called_once_with()
        mock_listdir.assert_has_calls(
            [
                call('/test/upload/path/feedback_resource_comment'),
                call('/test/upload/path/feedback_utilization_comment'),
            ]
        )
        mock_comment_service.get_comment_attached_image_files.assert_called_once_with()
        mock_detail_service.get_comment_attached_image_files.assert_called_once_with()
        mock_delete_invalid_files.assert_has_calls(
            [
                call(
                    dry_run,
                    '/test/upload/path/feedback_resource_comment',
                    {'image3.png'},
                ),
                call(
                    dry_run,
                    '/test/upload/path/feedback_utilization_comment',
                    {'image2.png', 'image3.png'},
                ),
            ]
        )

    @patch('ckanext.feedback.command.feedback.click.secho')
    @patch('ckanext.feedback.command.feedback.handle_file_deletion')
    def test_delete_invalid_files(self, mock_handle_file_deletion, mock_secho):
        dry_run = False
        dir_path = '/test/upload/path/feedback_resource_comment'
        invalid_files = {'image3.png'}

        mock_handle_file_deletion.return_value = None

        delete_invalid_files(dry_run, dir_path, invalid_files)

        mock_secho.assert_called_once_with(
            f"Found {len(invalid_files)} unwanted files in: {dir_path}", fg='yellow'
        )
        mock_handle_file_deletion.assert_called_once_with(
            dry_run, '/test/upload/path/feedback_resource_comment/image3.png'
        )

    @patch('ckanext.feedback.command.feedback.click.secho')
    def test_delete_invalid_files_with_none_invalid_files(self, mock_secho):
        dry_run = False
        dir_path = '/test/upload/path/feedback_resource_comment'
        invalid_files = None

        delete_invalid_files(dry_run, dir_path, invalid_files)

        mock_secho.assert_called_once_with(
            f"No files for deletion were found: {dir_path}", fg='green'
        )

    @patch('ckanext.feedback.command.feedback.os.remove')
    @patch('ckanext.feedback.command.feedback.click.secho')
    def test_handle_file_deletion(self, mock_secho, mock_remove):
        dry_run = False
        file_path = '/test/upload/path/feedback_resource_comment/image3.png'

        handle_file_deletion(dry_run, file_path)

        mock_remove.assert_called_once_with(file_path)
        mock_secho.assert_called_once_with(f"Deleted: {file_path}", fg='green')

    @patch('ckanext.feedback.command.feedback.os.remove')
    @patch('ckanext.feedback.command.feedback.click.secho')
    def test_handle_file_deletion_with_exception(self, mock_secho, mock_remove):
        dry_run = False
        file_path = '/test/upload/path/feedback_resource_comment/image3.png'

        mock_remove.side_effect = Exception('Error message')

        handle_file_deletion(dry_run, file_path)

        mock_secho.assert_called_once_with(
            f"Deletion failure: {file_path}. Error message", fg='red', err=True
        )

    @patch('ckanext.feedback.command.feedback.click.secho')
    def test_handle_file_deletion_dry_run(self, mock_secho):
        dry_run = True
        file_path = '/test/upload/path/feedback_resource_comment/image3.png'

        handle_file_deletion(dry_run, file_path)

        mock_secho.assert_called_once_with(
            f"[DRY RUN] Deletion Schedule: {file_path}", fg='blue'
        )

    @patch('ckanext.feedback.command.feedback.generate_moral_check_log_excel_bytes')
    @patch('ckanext.feedback.command.feedback.click.secho')
    def test_moral_check_log(
        self, mock_secho, mock_generate_moral_check_log_excel_bytes
    ):
        mock_generate_moral_check_log_excel_bytes.return_value = MagicMock(
            getvalue=lambda: b'test data'
        )

        self.runner.invoke(feedback, ['moral-check-log'])

        mock_generate_moral_check_log_excel_bytes.assert_called_once_with(False)
        mock_secho.assert_called_once_with(
            'Exported moral check log to moral_check_log.xlsx', fg='green'
        )

    @patch('ckanext.feedback.command.feedback.generate_moral_check_log_excel_bytes')
    @patch('ckanext.feedback.command.feedback.click.secho')
    def test_moral_check_log_with_separation(
        self, mock_secho, mock_generate_moral_check_log_excel_bytes
    ):
        mock_generate_moral_check_log_excel_bytes.return_value = MagicMock(
            getvalue=lambda: b'test data'
        )

        self.runner.invoke(
            feedback,
            [
                'moral-check-log',
                '--separation',
                '--output',
                'moral_check_log_separation.xlsx',
            ],
        )

        mock_generate_moral_check_log_excel_bytes.assert_called_once_with(True)
        mock_secho.assert_called_once_with(
            'Exported moral check log to moral_check_log_separation.xlsx', fg='green'
        )

    @patch('ckanext.feedback.command.feedback.generate_moral_check_log_excel_bytes')
    @patch('ckanext.feedback.command.feedback.click.echo')
    def test_moral_check_log_exception(
        self, mock_echo, mock_generate_moral_check_log_excel_bytes
    ):
        mock_generate_moral_check_log_excel_bytes.side_effect = Exception(
            'test exception'
        )

        result = self.runner.invoke(feedback, ['moral-check-log'])

        assert result.exit_code != 0
        mock_generate_moral_check_log_excel_bytes.assert_called_once_with(False)
        mock_echo.assert_called_once_with("Error: test exception", err=True)
