import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from ckan.tests import factories

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
    UtilizationSummary,
)
from ckanext.feedback.services.admin import utilization as utilization_service


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


def get_registered_utilization_summary(resource_id):
    return (
        session.query(UtilizationSummary)
        .filter(UtilizationSummary.resource_id == resource_id)
        .first()
    )


@pytest.mark.db_test
class TestUtilization:
    def test_get_utilizations_query(self):
        organization = factories.Organization()

        org_list = [{'name': organization['name'], 'title': organization['title']}]

        query = utilization_service.get_utilizations_query(org_list)
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

    def test_get_simple_utilizations_query(self):
        organization = factories.Organization()

        org_list = [{'name': organization['name'], 'title': organization['title']}]

        query = utilization_service.get_simple_utilizations_query(org_list)
        sql_str = str(query.statement)

        assert "group_name" in sql_str
        assert "feedback_type" in sql_str
        assert "is_approved" in sql_str

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilizations_by_comment_ids(self):
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
            len(
                utilization_service.get_utilizations_by_comment_ids(
                    [comment_id, another_comment_id]
                )
            )
            == 2
        )
        assert (
            utilization_service.get_utilizations_by_comment_ids(
                [comment_id, another_comment_id]
            )[0].id
            == utilization_id
        )
        assert (
            utilization_service.get_utilizations_by_comment_ids(
                [comment_id, another_comment_id]
            )[1].id
            == another_utilization_id
        )

    def test_get_utilization_details_by_ids(self):
        package = factories.Dataset()
        resource = factories.Resource(package_id=package['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        register_utilization(utilization_id, resource['id'], title, description, True)

        utilization_id_list = [utilization_id]

        utilizations = utilization_service.get_utilization_details_by_ids(
            utilization_id_list
        )

        assert len(utilizations) == 1
        util = utilizations[0]
        assert util.id == utilization_id
        assert util.title == title
        assert util.description == description
        assert util.comment == 0
        assert util.approval
        assert util.resource.name == resource['name']
        assert util.resource.id == resource['id']
        assert util.resource.package.name == package['name']
        assert util.resource.package.owner_org == package['owner_org']

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

    def test_get_utilization_resource_ids(self):
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

        resource_ids = utilization_service.get_utilization_resource_ids(
            utilization_id_list
        )

        assert resource_ids == [resource['id']]

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch('ckanext.feedback.services.admin.utilization.session.bulk_update_mappings')
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

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_refresh_utilization_summary(self, resource, utilization):
        resource_ids = [resource['id']]

        utilization_service.refresh_utilization_summary(resource_ids)
        session.commit()

        utilization_summary = get_registered_utilization_summary(resource['id'])

        assert utilization_summary.utilization == 1
        assert utilization_summary.updated == datetime(2024, 1, 1, 15, 0, 0)
