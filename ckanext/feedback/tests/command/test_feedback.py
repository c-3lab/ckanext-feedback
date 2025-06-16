from unittest.mock import call, patch

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
    ResourceCommentReactions,
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
                ResourceLike.__table__,
                ResourceLikeMonthly.__table__,
                ResourceCommentReactions.__table__,
                DownloadSummary.__table__,
                DownloadMonthly.__table__,
            ],
            checkfirst=True,
        )

    def test_feedback_default(self):
        result = self.runner.invoke(feedback, ['init'])
        assert 'Initialize all modules: SUCCESS' in result.output
        assert engine.has_table(Utilization.__table__)
        assert engine.has_table(UtilizationComment.__table__)
        assert engine.has_table(UtilizationSummary.__table__)
        assert engine.has_table(IssueResolution.__table__)
        assert engine.has_table(IssueResolutionSummary.__table__)
        assert engine.has_table(ResourceComment.__table__)
        assert engine.has_table(ResourceCommentReply.__table__)
        assert engine.has_table(ResourceCommentSummary.__table__)
        assert engine.has_table(ResourceLike.__table__)
        assert engine.has_table(ResourceLikeMonthly.__table__)
        assert engine.has_table(ResourceCommentReactions.__table__)
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
        assert engine.has_table(IssueResolution.__table__)
        assert engine.has_table(IssueResolutionSummary.__table__)
        assert not engine.has_table(ResourceComment.__table__)
        assert not engine.has_table(ResourceCommentReply.__table__)
        assert not engine.has_table(ResourceCommentSummary.__table__)
        assert not engine.has_table(ResourceLike.__table__)
        assert not engine.has_table(ResourceLikeMonthly.__table__)
        assert not engine.has_table(ResourceCommentReactions.__table__)
        assert not engine.has_table(DownloadSummary.__table__)
        assert not engine.has_table(DownloadMonthly.__table__)

    def test_feedback_resource(self):
        result = self.runner.invoke(feedback, ['init', '--modules', 'resource'])
        assert 'Initialize resource: SUCCESS' in result.output
        assert not engine.has_table(Utilization.__table__)
        assert not engine.has_table(UtilizationComment.__table__)
        assert not engine.has_table(UtilizationSummary.__table__)
        assert not engine.has_table(IssueResolution.__table__)
        assert not engine.has_table(IssueResolutionSummary.__table__)
        assert engine.has_table(ResourceComment.__table__)
        assert engine.has_table(ResourceCommentReply.__table__)
        assert engine.has_table(ResourceCommentSummary.__table__)
        assert engine.has_table(ResourceLike.__table__)
        assert engine.has_table(ResourceLikeMonthly.__table__)
        assert engine.has_table(ResourceCommentReactions.__table__)
        assert not engine.has_table(DownloadSummary.__table__)
        assert not engine.has_table(DownloadMonthly.__table__)

    def test_feedback_download(self):
        result = self.runner.invoke(feedback, ['init', '--modules', 'download'])
        assert 'Initialize download: SUCCESS' in result.output
        assert not engine.has_table(Utilization.__table__)
        assert not engine.has_table(UtilizationComment.__table__)
        assert not engine.has_table(UtilizationSummary.__table__)
        assert not engine.has_table(IssueResolution.__table__)
        assert not engine.has_table(IssueResolutionSummary.__table__)
        assert not engine.has_table(ResourceComment.__table__)
        assert not engine.has_table(ResourceCommentReply.__table__)
        assert not engine.has_table(ResourceCommentSummary.__table__)
        assert not engine.has_table(ResourceLike.__table__)
        assert not engine.has_table(ResourceLikeMonthly.__table__)
        assert not engine.has_table(ResourceCommentReactions.__table__)
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
        assert not engine.has_table(IssueResolution.__table__)
        assert not engine.has_table(IssueResolutionSummary.__table__)
        assert not engine.has_table(ResourceComment.__table__)
        assert not engine.has_table(ResourceCommentReply.__table__)
        assert not engine.has_table(ResourceCommentSummary.__table__)
        assert not engine.has_table(ResourceLike.__table__)
        assert not engine.has_table(ResourceLikeMonthly.__table__)
        assert not engine.has_table(ResourceCommentReactions.__table__)
        assert not engine.has_table(DownloadSummary.__table__)
        assert not engine.has_table(DownloadMonthly.__table__)

    @patch('ckanext.feedback.command.feedback.config')
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
        mock_config,
    ):
        dry_run = False

        mock_config.get.return_value = '/test/upload/path'
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

        mock_config.get.assert_called_once_with('ckan.feedback.storage_path')
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
        print(mock_delete_invalid_files.call_args_list)
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
