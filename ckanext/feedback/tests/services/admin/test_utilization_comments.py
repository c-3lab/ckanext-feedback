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


def get_registered_utilization(resource_id):
    return (
        session.query(
            Utilization.id,
            Utilization.approval,
            Utilization.approved,
            Utilization.approval_user_id,
        )
        .filter(Utilization.resource_id == resource_id)
        .all()
    )


def get_registered_utilization_comment(utilization_id):
    return (
        session.query(
            UtilizationComment.id,
            UtilizationComment.utilization_id,
            UtilizationComment.category,
            UtilizationComment.content,
            UtilizationComment.created,
            UtilizationComment.approval,
            UtilizationComment.approved,
            UtilizationComment.approval_user_id,
        )
        .filter(UtilizationComment.utilization_id == utilization_id)
        .all()
    )


engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestUtilizationComments:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_utilization_comments_query(self):
        organization = factories.Organization()

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

    def test_get_simple_utilization_comments_query(self):
        organization = factories.Organization()

        org_list = [{'name': organization['name'], 'title': organization['title']}]

        query = utilization_comments.get_simple_utilization_comments_query(org_list)
        sql_str = str(query.statement)

        assert "group_name" in sql_str
        assert "feedback_type" in sql_str
        assert "is_approved" in sql_str

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilization_comments(self):
        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

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

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilization_comment_ids(self):
        resource = factories.Resource()

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        register_utilization(utilization_id, resource['id'], title, description, True)

        comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()

        register_utilization_comment(
            comment_id,
            utilization_id,
            category,
            content,
            created,
            False,
            None,
            None,
        )

        session.commit()

        comment_id_list = [comment_id]

        utilization_comment_ids = utilization_comments.get_utilization_comment_ids(
            comment_id_list
        )

        assert utilization_comment_ids == [comment_id]

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch(
        'ckanext.feedback.services.admin.utilization_comments.'
        'session.bulk_update_mappings'
    )
    def test_approve_utilization_comments(self, mock_mappings):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()

        register_utilization(utilization_id, resource['id'], title, description, True)
        register_utilization_comment(
            comment_id, utilization_id, category, content, created, False, None, None
        )

        session.commit()

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

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_delete_utilization_comments(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()

        register_utilization(utilization_id, resource['id'], title, description, True)
        register_utilization_comment(
            comment_id, utilization_id, category, content, created, False, None, None
        )

        session.commit()

        utilization_comment = get_registered_utilization_comment(utilization_id)
        assert len(utilization_comment) == 1

        utilization_comments.delete_utilization_comments([comment_id])

        utilization_comment = get_registered_utilization_comment(utilization_id)
        assert len(utilization_comment) == 0

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
        self, mock_mappings, mock_get_utilization_comments
    ):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

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
