from ckanext.feedback.components.comment import CommentComponent
from ckanext.feedback.models.types import CommentCategory


class TestCommentComponent:
    def test_create_category_icon(self):
        category = CommentCategory.REQUEST.value

        icon = CommentComponent.create_category_icon(category)

        assert icon == '<i class="fas fa-lightbulb" style="color: #f0ad4e;"></i>'
