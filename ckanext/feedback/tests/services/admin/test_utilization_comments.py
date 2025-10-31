import uuid
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
)
from ckanext.feedback.services.admin import utilization_comments


def register_utilization(id, resource_id, title, description, approval):
    utilization = Utilization(
        id=id,
        resource_id=resource_id,
        title=title,
        description=description,
        approval=approval,
    )
    session.add(utilization)
    session.commit()


def register_utilization_comment(
    id, utilization_id, category, content, created, approval, approved, approval_user_id
):
    utilization_comment = UtilizationComment(
        id=id,
        utilization_id=utilization_id,
        category=category,
        content=content,
        created=created,
        approval=approval,
        approved=approved,
        approval_user_id=approval_user_id,
    )
    session.add(utilization_comment)
    session.commit()


def get_registered_utilization(resource_id):
    return (
        session.query(Utilization).filter(Utilization.resource_id == resource_id).all()
    )


@pytest.mark.db_test
class TestUtilizationComments:
    def test_get_utilization_comments_query(self, organization):
        org_list = [{'name': organization['name'], 'title': organization['title']}]

        query = utilization_comments.get_utilization_comments_query(org_list)
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

    def test_get_simple_utilization_comments_query(self, organization):
        org_list = [{'name': organization['name'], 'title': organization['title']}]

        query = utilization_comments.get_simple_utilization_comments_query(org_list)
        sql_str = str(query.statement)

        assert "group_name" in sql_str
        assert "feedback_type" in sql_str
        assert "is_approved" in sql_str

    def test_get_utilization_comments(self, resource):
        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()
        approved = datetime.now()

        assert utilization_comments.get_utilization_comments(id) == 0

        register_utilization(id, resource['id'], title, description, True)
        register_utilization_comment(
            comment_id, id, category, content, created, True, approved, None
        )
        session.commit()

        assert utilization_comments.get_utilization_comments(id) == 1

    def test_get_utilization_comment_ids(self, resource):
        utilization_id = str(uuid.uuid4())
        utilization_title = 'test title'
        utilization_description = 'test description'

        register_utilization(
            utilization_id,
            resource['id'],
            utilization_title,
            utilization_description,
            False,
        )

        comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()

        register_utilization_comment(
            comment_id, utilization_id, category, content, created, False, None, None
        )

        comment_id_list = [comment_id]

        comment_ids = utilization_comments.get_utilization_comment_ids(comment_id_list)

        assert comment_ids == [comment_id]

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch(
        'ckanext.feedback.services.admin.utilization_comments.'
        'session.bulk_update_mappings'
    )
    def test_approve_utilization_comments(self, mock_mappings, resource):
        utilization_id = str(uuid.uuid4())
        utilization_title = 'test title'
        utilization_description = 'test description'

        register_utilization(
            utilization_id,
            resource['id'],
            utilization_title,
            utilization_description,
            False,
        )

        comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()

        register_utilization_comment(
            comment_id, utilization_id, category, content, created, False, None, None
        )

        comment_id_list = [comment_id]

        utilization_comments.approve_utilization_comments(comment_id_list, None)

        expected_args = (
            UtilizationComment,
            [
                {
                    'id': comment_id,
                    'approval': True,
                    'approved': datetime.now(),
                    'approval_user_id': None,
                }
            ],
        )

        assert mock_mappings.call_args[0] == expected_args

    @patch('ckanext.feedback.services.admin.utilization_comments.session')
    @patch('ckanext.feedback.services.admin.utilization_comments.detail_service')
    @patch('ckanext.feedback.services.admin.utilization_comments.os.path.exists')
    @patch('ckanext.feedback.services.admin.utilization_comments.os.remove')
    def test_delete_utilization_comments(
        self,
        mock_remove,
        mock_exists,
        mock_detail_service,
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

        mock_detail_service.get_attached_image_path.side_effect = [
            "/fake/path/image1.png",
            "/fake/path/image2.png",
            None,
        ]
        mock_exists.side_effect = [True, False]

        utilization_comments.delete_utilization_comments(comment_id_list)

        mock_session.query.assert_called()
        mock_filter.all.assert_called_once()
        mock_detail_service.get_attached_image_path.assert_has_calls(
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
        'ckanext.feedback.services.admin.utilization_comments.'
        'get_utilization_comments'
    )
    @patch(
        'ckanext.feedback.services.admin.utilization_comments.'
        'session.bulk_update_mappings'
    )
    def test_refresh_utilizations_comments(
        self, mock_mappings, mock_get_utilization_comments, resource
    ):
        utilization_id = str(uuid.uuid4())
        another_utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        register_utilization(utilization_id, resource['id'], title, description, True)
        register_utilization(
            another_utilization_id, resource['id'], title, description, True
        )

        session.commit()

        mock_get_utilization_comments.return_value = 0
        utilization_comments.refresh_utilizations_comments(
            [
                get_registered_utilization(resource['id'])[0],
                get_registered_utilization(resource['id'])[1],
            ]
        )

        expected_args = (
            Utilization,
            [
                {
                    'id': utilization_id,
                    'comment': 0,
                    'updated': datetime.now(),
                },
                {
                    'id': another_utilization_id,
                    'comment': 0,
                    'updated': datetime.now(),
                },
            ],
        )

        assert mock_get_utilization_comments.call_count == 2
        assert mock_mappings.call_args[0] == expected_args
