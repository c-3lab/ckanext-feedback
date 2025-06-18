from ckanext.feedback.models.types import CommentCategory


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

    @staticmethod
    def create_category_icon(category):
        return CommentComponent.category_icon[category]
