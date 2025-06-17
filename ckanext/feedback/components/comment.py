from ckan.common import _

from ckanext.feedback.models.types import CommentCategory, ResourceCommentResponseStatus


class CommentComponent:
    category_icon = {
        CommentCategory.REQUEST.value: (
            '<i class="fas fa-lightbulb" style="color: #f0ad4e;"></i>'
        ),
        CommentCategory.QUESTION.value: (
            '<i class="fas fa-question-circle" style="color: #007bff;"></i>'
        ),
        CommentCategory.THANK.value: (
            '<i class="fas fa-heart" style="color: #e83e8c;"></i>'
        ),
    }

    def __init__(self, comment_id):
        self.comment_id = comment_id

        status_not_started = _('Not Started')
        status_in_progress = _('In Progress')
        status_completed = _('Completed')
        status_rejected = _('Rejected')

        self.status_badge = {
            ResourceCommentResponseStatus.STATUS_NONE.value: '',
            ResourceCommentResponseStatus.NOT_STARTED.value: (
                f'<span id="comment-badge-{self.comment_id}" '
                'class="badge badge-pill badge-not-started" '
                f'data-status="status-not-started">{status_not_started}</span>'
            ),
            ResourceCommentResponseStatus.IN_PROGRESS.value: (
                f'<span id="comment-badge-{self.comment_id}" '
                'class="badge badge-pill badge-in-progress" '
                f'data-status="status-in-progress">{status_in_progress}</span>'
            ),
            ResourceCommentResponseStatus.COMPLETED.value: (
                f'<span id="comment-badge-{self.comment_id}" '
                'class="badge badge-pill badge-completed" '
                f'data-status="status-completed">{status_completed}</span>'
            ),
            ResourceCommentResponseStatus.REJECTED.value: (
                f'<span id="comment-badge-{self.comment_id}" '
                'class="badge badge-pill badge-rejected" '
                f'data-status="status-rejected">{status_rejected}</span>'
            ),
        }

    @staticmethod
    def create_category_icon(category):
        return CommentComponent.category_icon[category]

    def create_status_badge(self, status):
        return self.status_badge[status]
