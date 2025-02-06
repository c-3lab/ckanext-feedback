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
from ckanext.feedback.services.management import utilization as utilization_service


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


engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestUtilization:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_utilizations_query(self):
        query = utilization_service.get_utilizations_query()

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

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilizations(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        another_utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        comment_id = str(uuid.uuid4())
        another_comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()
        approved = datetime.now()

        register_utilization(utilization_id, resource['id'], title, description, True)
        register_utilization(
            another_utilization_id, resource['id'], title, description, True
        )

        register_utilization_comment(
            comment_id, utilization_id, category, content, created, True, approved, None
        )

        register_utilization_comment(
            another_comment_id,
            another_utilization_id,
            category,
            content,
            created,
            True,
            approved,
            None,
        )

        session.commit()

        assert (
            len(utilization_service.get_utilizations([comment_id, another_comment_id]))
            == 2
        )
        assert (
            utilization_service.get_utilizations([comment_id, another_comment_id])[0].id
            == utilization_id
        )
        assert (
            utilization_service.get_utilizations([comment_id, another_comment_id])[1].id
            == another_utilization_id
        )

    def test_get_utilization_ids(self):
        resource = factories.Resource()

        utilization_id = str(uuid.uuid4())
        another_utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        register_utilization(utilization_id, resource['id'], title, description, False)
        register_utilization(
            another_utilization_id, resource['id'], title, description, True
        )

        session.commit()

        utilization_id_list = [utilization_id]

        utilization_ids = utilization_service.get_utilization_ids(utilization_id_list)

        assert utilization_ids == [utilization_id]

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch(
        'ckanext.feedback.services.management.utilization.session.bulk_update_mappings'
    )
    def test_approve_utilization(self, mock_mappings):
        resource = factories.Resource()

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        register_utilization(utilization_id, resource['id'], title, description, False)

        session.commit()

        utilization_id_list = [utilization_id]

        utilization_service.approve_utilization(utilization_id_list, None)

        expected_args = (
            Utilization,
            [
                {
                    'id': utilization_id,
                    'approval': True,
                    'approved': datetime.now(),
                    'approval_user_id': None,
                }
            ],
        )

        assert mock_mappings.call_args[0] == expected_args

    def test_delete_utilization(self):
        resource = factories.Resource()

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        register_utilization(utilization_id, resource['id'], title, description, False)

        session.commit()

        utilization = get_registered_utilization(resource['id'])
        assert len(utilization) == 1

        utilization_id_list = [utilization_id]
        utilization_service.delete_utilization(utilization_id_list)

        utilization = get_registered_utilization(resource['id'])
        assert len(utilization) == 0
