import enum
import importlib

from ckanext.feedback.models.types import CommentCategory as ModelCommentCategory
from ckanext.feedback.models.types import (
    ResourceCommentResponseStatus as ModelResourceCommentResponseStatus,
)

Migration000 = importlib.import_module(
    "ckanext.feedback.migration.feedback.versions.000_40bf9a900ef5_init"
)
Migration005 = importlib.import_module(
    "ckanext.feedback.migration.feedback.versions.005_87954668dbb2_"
)

MigrationResourceCommentCategory = Migration000.ResourceCommentCategory
MigrationUtilizationCommentCategory = Migration000.UtilizationCommentCategory
MigrationResourceCommentResponseStatus = Migration005.ResourceCommentResponseStatus


class TestCommentCategoryConsistency:
    def test_comment_category_type(self):
        assert isinstance(ModelCommentCategory, enum.EnumMeta)
        assert isinstance(MigrationResourceCommentCategory, enum.EnumMeta)
        assert isinstance(MigrationUtilizationCommentCategory, enum.EnumMeta)

    def test_comment_category_length(self):
        assert len(ModelCommentCategory) == len(MigrationResourceCommentCategory)
        assert len(ModelCommentCategory) == len(MigrationUtilizationCommentCategory)

    def test_comment_category_names(self):
        model_names = {category.name for category in ModelCommentCategory}
        migration_resource_names = {
            category.name for category in MigrationResourceCommentCategory
        }
        migration_utilization_names = {
            category.name for category in MigrationUtilizationCommentCategory
        }

        assert model_names == migration_resource_names
        assert model_names == migration_utilization_names

    def test_comment_category_values(self):
        model_values = {category.value for category in ModelCommentCategory}
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
        assert isinstance(ModelResourceCommentResponseStatus, enum.EnumMeta)
        assert isinstance(MigrationResourceCommentResponseStatus, enum.EnumMeta)

    def test_resource_comment_response_status_length(self):
        assert len(ModelResourceCommentResponseStatus) == len(
            MigrationResourceCommentResponseStatus
        )

    def test_resource_comment_response_status_names(self):
        model_names = {status.name for status in ModelResourceCommentResponseStatus}
        migration_names = {
            status.name for status in MigrationResourceCommentResponseStatus
        }

        assert model_names == migration_names

    def test_resource_comment_response_status_values(self):
        model_values = {status.value for status in ModelResourceCommentResponseStatus}
        migration_values = {
            status.value for status in MigrationResourceCommentResponseStatus
        }

        assert model_values == migration_values
