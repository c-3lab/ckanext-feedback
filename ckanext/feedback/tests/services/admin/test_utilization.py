import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
    UtilizationSummary,
)
from ckanext.feedback.services.admin import utilization as utilization_service


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

    def test_get_utilizations_query(self, organization):

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

    def test_get_simple_utilizations_query(self, organization):

        org_list = [{'name': organization['name'], 'title': organization['title']}]

        query = utilization_service.get_simple_utilizations_query(org_list)
        sql_str = str(query.statement)

        assert "group_name" in sql_str
        assert "feedback_type" in sql_str
        assert "is_approved" in sql_str

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilizations_by_comment_ids(self, resource, multiple_utilizations):
        utils = multiple_utilizations(count=2)
        util1 = utils[0]
        util2 = utils[1]

        comment_id1 = str(uuid.uuid4())
        comment1 = UtilizationComment(
            id=comment_id1,
            utilization_id=util1.id,
            category=UtilizationCommentCategory.QUESTION,
            content='test content 1',
            created=datetime.now(),
            approval=True,
            approved=datetime.now(),
        )
        session.add(comment1)

        comment_id2 = str(uuid.uuid4())
        comment2 = UtilizationComment(
            id=comment_id2,
            utilization_id=util2.id,
            category=UtilizationCommentCategory.QUESTION,
            content='test content 2',
            created=datetime.now(),
            approval=True,
            approved=datetime.now(),
        )
        session.add(comment2)

        session.commit()

        result = utilization_service.get_utilizations_by_comment_ids(
            [comment_id1, comment_id2]
        )
        assert len(result) == 2
        assert result[0].id == util1.id
        assert result[1].id == util2.id

    def test_get_utilization_details_by_ids(
        self, dataset, resource, multiple_utilizations
    ):
        utils = multiple_utilizations(count=1)
        util = utils[0]

        title = 'test_title_0'
        description = 'test_description_0'

        utilization_id_list = [util.id]
        utilizations = utilization_service.get_utilization_details_by_ids(
            utilization_id_list
        )

        assert len(utilizations) == 1
        result_util = utilizations[0]
        assert result_util.id == util.id
        assert result_util.title == title
        assert result_util.description == description
        assert result_util.comment == 0
        assert result_util.approval
        assert result_util.resource.name == resource['name']
        assert result_util.resource.id == resource['id']
        assert result_util.resource.package.name == dataset['name']
        assert result_util.resource.package.owner_org == dataset['owner_org']

    def test_get_utilization_ids(self, resource, multiple_utilizations):
        utils = multiple_utilizations(count=1, approval=False)
        util1 = utils[0]

        session.commit()

        utilization_id_list = [util1.id]
        utilization_ids = utilization_service.get_utilization_ids(utilization_id_list)

        assert utilization_ids == [util1.id]

    def test_get_utilization_resource_ids(self, resource, multiple_utilizations):
        utils = multiple_utilizations(count=1, approval=False)
        util1 = utils[0]

        session.commit()

        utilization_id_list = [util1.id]
        resource_ids = utilization_service.get_utilization_resource_ids(
            utilization_id_list
        )

        assert resource_ids == [resource['id']]

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch('ckanext.feedback.services.admin.utilization.session.bulk_update_mappings')
    def test_approve_utilization(
        self, mock_mappings, resource, multiple_utilizations, user
    ):
        utils = multiple_utilizations(count=1, approval=False)
        util = utils[0]

        session.commit()

        utilization_id_list = [util.id]
        approval_user_id = user['id']
        utilization_service.approve_utilization(utilization_id_list, approval_user_id)

        expected_args = (
            Utilization,
            [
                {
                    'id': util.id,
                    'approval': True,
                    'approved': datetime.now(),
                    'approval_user_id': approval_user_id,
                }
            ],
        )

        assert mock_mappings.call_args[0] == expected_args

    def test_delete_utilization(self, resource, multiple_utilizations):
        utils = multiple_utilizations(count=1, approval=False)
        util = utils[0]

        session.commit()

        utilization = get_registered_utilization(resource['id'])
        assert len(utilization) == 1

        utilization_id_list = [util.id]
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
