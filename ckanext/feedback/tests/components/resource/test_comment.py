from ckanext.feedback.components.resource.comment import ResourceCommentComponent
from ckanext.feedback.models.resource_comment import (
    ResourceCommentCategory,
    ResourceCommentResponseStatus,
)


class TestResourceCommentComponent:
    def test_create_category_icon(self):
        category = ResourceCommentCategory.REQUEST.value

        icon = ResourceCommentComponent.create_category_icon(category)

        assert icon == '<i class="fas fa-lightbulb" style="color: #f0ad4e;"></i>'

    def test_create_status_badge(self):
        status = ResourceCommentResponseStatus.COMPLETED.value
        comment_id = 'comment-id'
        component = ResourceCommentComponent(comment_id)

        badge = component.create_status_badge(status)

        expected_badge = (
            '<span id="comment-badge-comment-id" class="badge badge-pill '
            'badge-completed" data-status="status-completed">Completed</span>'
        )

        assert badge == expected_badge
