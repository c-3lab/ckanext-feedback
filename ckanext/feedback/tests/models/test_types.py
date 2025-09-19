import enum
import importlib

from ckanext.feedback.models import types as ModelTypes

Migration000 = importlib.import_module(
    "ckanext.feedback.migration.feedback.versions.000_40bf9a900ef5_init"
)
Migration005 = importlib.import_module(
    "ckanext.feedback.migration.feedback.versions.005_87954668dbb2_"
)
Migration008 = importlib.import_module(
    "ckanext.feedback.migration.feedback.versions.008_c64333d190eb_"
)

MigrationResourceCommentCategory = Migration000.ResourceCommentCategory
MigrationUtilizationCommentCategory = Migration000.UtilizationCommentCategory
MigrationResourceCommentResponseStatus = Migration005.ResourceCommentResponseStatus
MigrationMoralCheckAction = Migration008.MoralCheckAction


class TestCommentCategoryConsistency:
    def test_comment_category_type(self):
        assert isinstance(ModelTypes.CommentCategory, enum.EnumMeta)
        assert isinstance(MigrationResourceCommentCategory, enum.EnumMeta)
        assert isinstance(MigrationUtilizationCommentCategory, enum.EnumMeta)

    def test_comment_category_length(self):
        assert len(ModelTypes.CommentCategory) == len(MigrationResourceCommentCategory)
        assert len(ModelTypes.CommentCategory) == len(
            MigrationUtilizationCommentCategory
        )

    def test_comment_category_names(self):
        model_names = {category.name for category in ModelTypes.CommentCategory}
        migration_resource_names = {
            category.name for category in MigrationResourceCommentCategory
        }
        migration_utilization_names = {
            category.name for category in MigrationUtilizationCommentCategory
        }

        assert model_names == migration_resource_names
        assert model_names == migration_utilization_names

    def test_comment_category_values(self):
        model_values = {category.value for category in ModelTypes.CommentCategory}
        migration_resource_values = {
            category.value for category in MigrationResourceCommentCategory
        }
        migration_utilization_values = {
            category.value for category in MigrationUtilizationCommentCategory
        }

        assert model_values == migration_resource_values
        assert model_values == migration_utilization_values


class TestResourceCommentResponseStatusConsistency:
    def test_resource_comment_response_status_type(self):
        assert isinstance(ModelTypes.ResourceCommentResponseStatus, enum.EnumMeta)
        assert isinstance(MigrationResourceCommentResponseStatus, enum.EnumMeta)

    def test_resource_comment_response_status_length(self):
        assert len(ModelTypes.ResourceCommentResponseStatus) == len(
            MigrationResourceCommentResponseStatus
        )

    def test_resource_comment_response_status_names(self):
        model_names = {
            status.name for status in ModelTypes.ResourceCommentResponseStatus
        }
        migration_names = {
            status.name for status in MigrationResourceCommentResponseStatus
        }

        assert model_names == migration_names

    def test_resource_comment_response_status_values(self):
        model_values = {
            status.value for status in ModelTypes.ResourceCommentResponseStatus
        }
        migration_values = {
            status.value for status in MigrationResourceCommentResponseStatus
        }

        assert model_values == migration_values


class TestMoralCheckActionConsistency:
    def test_moral_check_action_type(self):
        assert isinstance(ModelTypes.MoralCheckAction, enum.EnumMeta)
        assert isinstance(MigrationMoralCheckAction, enum.EnumMeta)

    def test_moral_check_action_length(self):
        assert len(ModelTypes.MoralCheckAction) == len(MigrationMoralCheckAction)

    def test_moral_check_action_names(self):
        model_names = {action.name for action in ModelTypes.MoralCheckAction}
        migration_names = {action.name for action in MigrationMoralCheckAction}

        assert model_names == migration_names

    def test_moral_check_action_values(self):
        model_values = {action.value for action in ModelTypes.MoralCheckAction}
        migration_values = {action.value for action in MigrationMoralCheckAction}

        assert model_values == migration_values
