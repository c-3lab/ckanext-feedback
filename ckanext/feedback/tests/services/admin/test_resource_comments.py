import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from ckan import model
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
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


def get_resource_comment_summary(resource_id):
    resource_comment_summary = (
        session.query(ResourceCommentSummary)
        .filter(ResourceCommentSummary.resource_id == resource_id)
        .first()
    )
    return resource_comment_summary


engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestResourceComments:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_resource_comments_query(self):
        organization = factories.Organization()

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

    def test_get_simple_resource_comments_query(self):
        organization = factories.Organization()

        org_list = [{'name': organization['name'], 'title': organization['title']}]

        query = resource_comments.get_simple_resource_comments_query(org_list)
        sql_str = str(query.statement)

        assert "group_name" in sql_str
        assert "feedback_type" in sql_str
        assert "is_approved" in sql_str

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_resource_comment_ids(self):
        resource = factories.Resource()

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

    def test_get_resource_comment_summaries(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        another_resource = factories.Resource(package_id=dataset['id'])

        category = ResourceCommentCategory.QUESTION

        comment.create_resource_comment(resource['id'], category, 'test content 1', 1)
        comment.create_resource_comment(
            another_resource['id'], category, 'test content 2', 5
        )
        summary.create_resource_summary(resource['id'])
        summary.create_resource_summary(another_resource['id'])

        resource_comment = comment.get_resource_comments(resource['id'], None)
        another_resource_comment = comment.get_resource_comments(
            another_resource['id'], None
        )

        comment.approve_resource_comment(resource_comment[0].id, None)
        comment.approve_resource_comment(another_resource_comment[0].id, None)

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
    def test_approve_resource_comments(self, mock_mappings):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

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

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_delete_resource_comments(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        category = ResourceCommentCategory.QUESTION

        comment.create_resource_comment(resource['id'], category, 'test content 1', 1)
        resource_comment = comment.get_resource_comments(resource['id'], None)

        session.commit()

        comment_id_list = [resource_comment[0].id]
        assert len(resource_comment) == 1

        resource_comments.delete_resource_comments(comment_id_list)

        resource_comment = comment.get_resource_comments(resource['id'], None)
        assert len(resource_comment) == 0

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch(
        'ckanext.feedback.services.admin.resource_comments.'
        'session.bulk_update_mappings'
    )
    def test_refresh_resource_comments(self, mock_mappings):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        another_resource = factories.Resource(package_id=dataset['id'])

        category = ResourceCommentCategory.QUESTION

        comment.create_resource_comment(resource['id'], category, 'test content 1', 1)
        comment.create_resource_comment(
            another_resource['id'], category, 'test content 2', 5
        )
        summary.create_resource_summary(resource['id'])
        summary.create_resource_summary(another_resource['id'])

        resource_comment = comment.get_resource_comments(resource['id'], None)
        another_resource_comment = comment.get_resource_comments(
            another_resource['id'], None
        )

        comment.approve_resource_comment(resource_comment[0].id, None)
        comment.approve_resource_comment(another_resource_comment[0].id, None)

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
