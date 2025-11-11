import uuid
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentCategory,
    ResourceCommentSummary,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.services.admin import resource_comments
from ckanext.feedback.services.resource import comment, summary


def register_resource_comment(
    id,
    resource_id,
    category,
    content,
    rating,
    created,
    approval,
    approved,
    approval_user_id,
):
    resource_comment = ResourceComment(
        id=id,
        resource_id=resource_id,
        category=category,
        content=content,
        rating=rating,
        created=created,
        approval=approval,
        approved=approved,
        approval_user_id=approval_user_id,
    )
    session.add(resource_comment)
    session.commit()


def get_resource_comment_summary(resource_id):
    resource_comment_summary = (
        session.query(ResourceCommentSummary)
        .filter(ResourceCommentSummary.resource_id == resource_id)
        .first()
    )
    return resource_comment_summary


@pytest.mark.db_test
class TestResourceComments:
    def test_get_resource_comments_query(self, organization):
        org_list = [{'name': organization['name'], 'title': organization['title']}]

        query = resource_comments.get_resource_comments_query(org_list)
        sql_str = str(query.statement)

        assert "group_name" in sql_str
        assert "package_name" in sql_str
        assert "package_title" in sql_str
        assert "owner_org" in sql_str
        assert "resource_id" in sql_str
        assert "resource_name" in sql_str
        assert "utilization_id" in sql_str
        assert "feedback_type" in sql_str
        assert "comment_id" in sql_str
        assert "content" in sql_str
        assert "created" in sql_str
        assert "is_approved" in sql_str

    def test_get_simple_resource_comments_query(self, organization):
        org_list = [{'name': organization['name'], 'title': organization['title']}]

        query = resource_comments.get_simple_resource_comments_query(org_list)
        sql_str = str(query.statement)

        assert "group_name" in sql_str
        assert "feedback_type" in sql_str
        assert "is_approved" in sql_str

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_resource_comment_ids(self, resource):
        comment_id = str(uuid.uuid4())
        category = ResourceCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()

        register_resource_comment(
            comment_id,
            resource['id'],
            category,
            content,
            None,
            created,
            False,
            None,
            None,
        )

        session.commit()

        comment_id_list = [comment_id]

        comment_ids = resource_comments.get_resource_comment_ids(comment_id_list)

        assert comment_ids == [comment_id]

    def test_get_resource_comment_summaries(self, dataset):
        # Create 2 resources for this test
        from ckan.tests import factories

        resource = factories.Resource(package_id=dataset['id'])
        another_resource = factories.Resource(package_id=dataset['id'])

        category = ResourceCommentCategory.QUESTION

        comment.create_resource_comment(resource['id'], category, 'test content 1', 1)
        comment.create_resource_comment(
            another_resource['id'], category, 'test content 2', 5
        )
        session.commit()
        summary.create_resource_summary(resource['id'])
        summary.create_resource_summary(another_resource['id'])
        session.commit()

        resource_comment = comment.get_resource_comments(resource['id'], None)
        another_resource_comment = comment.get_resource_comments(
            another_resource['id'], None
        )

        comment.approve_resource_comment(resource_comment[0].id, None)
        comment.approve_resource_comment(another_resource_comment[0].id, None)
        session.commit()

        summary.refresh_resource_summary(resource['id'])
        summary.refresh_resource_summary(another_resource['id'])
        session.commit()

        comment_id_list = [resource_comment[0].id, another_resource_comment[0].id]

        resource_comment_summaries = resource_comments.get_resource_comment_summaries(
            comment_id_list
        )

        assert len(resource_comment_summaries) == 2
        assert resource_comment_summaries[0].comment == 1
        assert resource_comment_summaries[1].comment == 1

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch(
        'ckanext.feedback.services.admin.resource_comments.'
        'session.bulk_update_mappings'
    )
    def test_approve_resource_comments(self, mock_mappings, resource):
        category = ResourceCommentCategory.QUESTION

        comment.create_resource_comment(resource['id'], category, 'test content 1', 1)
        resource_comment = comment.get_resource_comments(resource['id'], None)

        session.commit()

        comment_id_list = [resource_comment[0].id]

        resource_comments.approve_resource_comments(comment_id_list, None)

        expected_args = (
            ResourceComment,
            [
                {
                    'id': resource_comment[0].id,
                    'approval': True,
                    'approved': datetime.now(),
                    'approval_user_id': None,
                }
            ],
        )

        assert mock_mappings.call_args[0] == expected_args

    @patch('ckanext.feedback.services.admin.resource_comments.session')
    @patch('ckanext.feedback.services.admin.resource_comments.comment_service')
    @patch('ckanext.feedback.services.admin.resource_comments.os.path.exists')
    @patch('ckanext.feedback.services.admin.resource_comments.os.remove')
    def test_delete_resource_comments(
        self,
        mock_remove,
        mock_exists,
        mock_comment_service,
        mock_session,
    ):
        comment_id_list = [1, 2, 3]

        mock_comment1 = MagicMock()
        mock_comment1.attached_image_filename = "image1.png"
        mock_comment2 = MagicMock()
        mock_comment2.attached_image_filename = "image2.png"
        mock_comment3 = MagicMock()
        mock_comment3.attached_image_filename = None

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = [mock_comment1, mock_comment2, mock_comment3]
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        mock_comment_service.get_attached_image_path.side_effect = [
            "/fake/path/image1.png",
            "/fake/path/image2.png",
            None,
        ]
        mock_exists.side_effect = [True, False]

        resource_comments.delete_resource_comments(comment_id_list)

        mock_session.query.assert_called()
        mock_filter.all.assert_called_once()
        mock_comment_service.get_attached_image_path.assert_has_calls(
            [
                call("image1.png"),
                call("image2.png"),
            ]
        )
        mock_exists.assert_has_calls(
            [
                call("/fake/path/image1.png"),
                call("/fake/path/image2.png"),
            ]
        )
        mock_remove.assert_called_once_with("/fake/path/image1.png")
        mock_filter.delete.assert_called_once_with(synchronize_session='fetch')

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch(
        'ckanext.feedback.services.admin.resource_comments.'
        'session.bulk_update_mappings'
    )
    def test_refresh_resource_comments(self, mock_mappings, dataset):
        # Create 2 resources for this test
        from ckan.tests import factories

        resource = factories.Resource(package_id=dataset['id'])
        another_resource = factories.Resource(package_id=dataset['id'])

        category = ResourceCommentCategory.QUESTION

        comment.create_resource_comment(resource['id'], category, 'test content 1', 1)
        comment.create_resource_comment(
            another_resource['id'], category, 'test content 2', 5
        )
        session.commit()
        summary.create_resource_summary(resource['id'])
        summary.create_resource_summary(another_resource['id'])
        session.commit()

        resource_comment = comment.get_resource_comments(resource['id'], None)
        another_resource_comment = comment.get_resource_comments(
            another_resource['id'], None
        )

        comment.approve_resource_comment(resource_comment[0].id, None)
        comment.approve_resource_comment(another_resource_comment[0].id, None)
        session.commit()

        summary.refresh_resource_summary(resource['id'])
        summary.refresh_resource_summary(another_resource['id'])
        session.commit()

        resource_comment_summary = get_resource_comment_summary(resource['id'])
        another_resource_comment_summary = get_resource_comment_summary(
            another_resource['id']
        )

        resource_comment_summaries = [
            resource_comment_summary,
            another_resource_comment_summary,
        ]

        resource_comments.refresh_resources_comments(resource_comment_summaries)

        expected_mapping = [
            {
                'id': resource_comment_summary.id,
                'comment': 1,
                'rating_comment': 1,
                'rating': 1,
                'updated': datetime.now(),
            },
            {
                'id': another_resource_comment_summary.id,
                'comment': 1,
                'rating_comment': 1,
                'rating': 5,
                'updated': datetime.now(),
            },
        ]

        assert mock_mappings.call_args[0] == (ResourceCommentSummary, expected_mapping)

        resource_comments.delete_resource_comments(
            [resource_comment[0].id, another_resource_comment[0].id]
        )
        resource_comments.refresh_resources_comments(resource_comment_summaries)
        session.commit()
        expected_mapping = [
            {
                'id': resource_comment_summary.id,
                'comment': 0,
                'rating_comment': 0,
                'rating': 0,
                'updated': datetime.now(),
            },
            {
                'id': another_resource_comment_summary.id,
                'comment': 0,
                'rating_comment': 0,
                'rating': 0,
                'updated': datetime.now(),
            },
        ]

        assert mock_mappings.call_args[0] == (ResourceCommentSummary, expected_mapping)

    def test_get_resource_comment_replies_query_minimal(self):
        from ckan.tests import factories

        from ckanext.feedback.services.admin import resource_comments as rc

        org = factories.Organization()
        org_list = [{'name': org['name'], 'title': org['title']}]
        q = rc.get_resource_comment_replies_query(org_list)
        s = str(q.statement)
        assert "resource_comment_reply" in s

    def test_get_simple_resource_comment_replies_query_minimal(self):
        from ckan.tests import factories

        from ckanext.feedback.services.admin import resource_comments as rc

        org = factories.Organization()
        org_list = [{'name': org['name'], 'title': org['title']}]
        q = rc.get_simple_resource_comment_replies_query(org_list)
        s = str(q.statement)
        assert "resource_comment_reply" in s
