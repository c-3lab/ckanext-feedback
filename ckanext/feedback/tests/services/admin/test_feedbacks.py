import logging
import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from ckan import model
from ckan.tests import factories
from sqlalchemy import select, union_all

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentCategory,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
)
from ckanext.feedback.services.admin import feedbacks
from ckanext.feedback.services.admin import (
    resource_comments as resource_comments_service,
)
from ckanext.feedback.services.admin import utilization as utilization_service
from ckanext.feedback.services.admin import (
    utilization_comments as utilization_comments_service,
)

log = logging.getLogger(__name__)


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


engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestFeedbacks:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_apply_filters_to_query(self):
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=dataset['id'])

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

        org_list = [{'name': organization['name'], 'title': organization['title']}]
        resource_comments = resource_comments_service.get_resource_comments_query(
            org_list
        )
        utilizations = utilization_service.get_utilizations_query(org_list)
        utilization_comments = (
            utilization_comments_service.get_utilization_comments_query(org_list)
        )
        combined_query = union_all(
            resource_comments, utilizations, utilization_comments
        ).subquery()
        query = select(combined_query)

        active_filters = []
        expected_query = query
        returned_query = feedbacks.apply_filters_to_query(
            query, active_filters, org_list, combined_query
        )
        assert str(returned_query) == str(expected_query)

        active_filters = ['approved']
        expected_query = query.filter(combined_query.c.is_approved.is_(True))
        returned_query = feedbacks.apply_filters_to_query(
            query, active_filters, org_list, combined_query
        )
        assert str(returned_query) == str(expected_query)

        active_filters = ['unapproved']
        expected_query = query.filter(combined_query.c.is_approved.is_(False))
        returned_query = feedbacks.apply_filters_to_query(
            query, active_filters, org_list, combined_query
        )
        assert str(returned_query) == str(expected_query)

        active_filters = ['resource']
        expected_query = query.filter(
            combined_query.c.feedback_type == 'リソースコメント'
        )
        returned_query = feedbacks.apply_filters_to_query(
            query, active_filters, org_list, combined_query
        )
        assert str(returned_query) == str(expected_query)

        active_filters = ['utilization']
        expected_query = query.filter(combined_query.c.feedback_type == '利活用申請')
        returned_query = feedbacks.apply_filters_to_query(
            query, active_filters, org_list, combined_query
        )
        assert str(returned_query) == str(expected_query)

        active_filters = ['util-comment']
        expected_query = query.filter(
            combined_query.c.feedback_type == '利活用コメント'
        )
        returned_query = feedbacks.apply_filters_to_query(
            query, active_filters, org_list, combined_query
        )
        assert str(returned_query) == str(expected_query)

        active_filters = [organization['name']]
        expected_query = query.filter(
            combined_query.c.group_name == organization['name']
        )
        returned_query = feedbacks.apply_filters_to_query(
            query, active_filters, org_list, combined_query
        )
        assert str(returned_query) == str(expected_query)

        active_filters = ['unknown']
        expected_query = query
        returned_query = feedbacks.apply_filters_to_query(
            query, active_filters, org_list, combined_query
        )
        assert str(returned_query) == str(expected_query)

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_feedbacks(self):
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=dataset['id'])

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

        expected_feedback_list = [
            {
                'package_name': dataset['name'],
                'package_title': dataset['title'],
                'resource_id': resource['id'],
                'resource_name': resource['name'],
                'utilization_id': None,
                'feedback_type': 'リソースコメント',
                'comment_id': comment_id,
                'content': content,
                'created': datetime(2000, 1, 2, 3, 4),
                'is_approved': False,
            },
        ]

        org_list = [{'name': organization['name'], 'title': organization['title']}]

        feedback_list, total_count = feedbacks.get_feedbacks(org_list)
        assert feedback_list == expected_feedback_list
        assert total_count == 1

        sort = 'oldest'
        feedback_list, total_count = feedbacks.get_feedbacks(org_list, sort=sort)
        assert feedback_list == expected_feedback_list
        assert total_count == 1

        for i in range(20):
            comment_id = str(uuid.uuid4())

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

        expected_feedback_list = [
            {
                'package_name': dataset['name'],
                'package_title': dataset['title'],
                'resource_id': resource['id'],
                'resource_name': resource['name'],
                'utilization_id': None,
                'feedback_type': 'リソースコメント',
                'comment_id': comment_id,
                'content': content,
                'created': datetime(2000, 1, 2, 3, 4),
                'is_approved': False,
            },
        ]

        limit = 20
        offset = 20
        feedback_list, total_count = feedbacks.get_feedbacks(
            org_list, limit=limit, offset=offset
        )
        assert feedback_list == expected_feedback_list
        assert total_count == 21

    def test_get_approval_counts(self):
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=dataset['id'])

        category = ResourceCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()
        approved = datetime.now()

        register_resource_comment(
            str(uuid.uuid4()),
            resource['id'],
            category,
            content,
            None,
            created,
            True,
            approved,
            None,
        )
        register_resource_comment(
            str(uuid.uuid4()),
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

        active_filters = []
        org_list = [{'name': organization['name'], 'title': organization['title']}]
        resource_comment_query = (
            resource_comments_service.get_simple_resource_comments_query(org_list)
        )
        utilization_query = utilization_service.get_simple_utilizations_query(org_list)
        utilization_comment_query = (
            utilization_comments_service.get_simple_utilization_comments_query(org_list)
        )
        combined_query = union_all(
            resource_comment_query, utilization_query, utilization_comment_query
        )

        expected_results = {"approved": 1, "unapproved": 1}
        results = feedbacks.get_approval_counts(
            active_filters, org_list, combined_query
        )

        assert results == expected_results

    def test_get_type_counts(self):
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=dataset['id'])

        category = ResourceCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()

        register_resource_comment(
            str(uuid.uuid4()),
            resource['id'],
            category,
            content,
            None,
            created,
            False,
            None,
            None,
        )

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        register_utilization(utilization_id, resource['id'], title, description, False)

        category = UtilizationCommentCategory.QUESTION

        register_utilization_comment(
            str(uuid.uuid4()),
            utilization_id,
            category,
            content,
            created,
            False,
            None,
            None,
        )

        session.commit()

        active_filters = []
        org_list = [{'name': organization['name'], 'title': organization['title']}]
        resource_comment_query = (
            resource_comments_service.get_simple_resource_comments_query(org_list)
        )
        utilization_query = utilization_service.get_simple_utilizations_query(org_list)
        utilization_comment_query = (
            utilization_comments_service.get_simple_utilization_comments_query(org_list)
        )
        combined_query = union_all(
            resource_comment_query, utilization_query, utilization_comment_query
        )

        expected_results = {"resource": 1, "utilization": 1, "util-comment": 1}
        results = feedbacks.get_type_counts(active_filters, org_list, combined_query)

        assert results == expected_results

    def test_get_organization_counts(self):
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=dataset['id'])

        category = ResourceCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()

        register_resource_comment(
            str(uuid.uuid4()),
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

        active_filters = []
        org_list = [{'name': organization['name'], 'title': organization['title']}]
        resource_comment_query = (
            resource_comments_service.get_simple_resource_comments_query(org_list)
        )
        utilization_query = utilization_service.get_simple_utilizations_query(org_list)
        utilization_comment_query = (
            utilization_comments_service.get_simple_utilization_comments_query(org_list)
        )
        combined_query = union_all(
            resource_comment_query, utilization_query, utilization_comment_query
        )

        expected_results = {organization['name']: 1}
        results = feedbacks.get_organization_counts(
            active_filters, org_list, combined_query
        )

        assert results == expected_results

    @patch('ckanext.feedback.services.admin.feedbacks.get_approval_counts')
    @patch('ckanext.feedback.services.admin.feedbacks.get_type_counts')
    @patch('ckanext.feedback.services.admin.feedbacks.get_organization_counts')
    def test_get_feedbacks_total_count(
        self,
        mock_get_organization_counts,
        mock_get_type_counts,
        mock_get_approval_counts,
    ):
        organization = factories.Organization()

        mock_get_approval_counts.return_value = {"approved": 1, "unapproved": 1}
        mock_get_type_counts.return_value = {
            "resource": 1,
            "utilization": 1,
            "util-comment": 1,
        }
        mock_get_organization_counts.return_value = {organization['name']: 1}

        active_filters = []
        org_list = [{'name': organization['name'], 'title': organization['title']}]

        filter_set_name = 'Status'
        feedbacks.get_feedbacks_total_count(filter_set_name, active_filters, org_list)
        mock_get_approval_counts.assert_called_once()
        mock_get_type_counts.assert_not_called()
        mock_get_organization_counts.assert_not_called()
        mock_get_approval_counts.reset_mock()

        filter_set_name = 'Type'
        feedbacks.get_feedbacks_total_count(filter_set_name, active_filters, org_list)
        mock_get_approval_counts.assert_not_called()
        mock_get_type_counts.assert_called_once()
        mock_get_organization_counts.assert_not_called()
        mock_get_type_counts.reset_mock()

        filter_set_name = 'Organization'
        feedbacks.get_feedbacks_total_count(filter_set_name, active_filters, org_list)
        mock_get_approval_counts.assert_not_called()
        mock_get_type_counts.assert_not_called()
        mock_get_organization_counts.assert_called_once()
        mock_get_organization_counts.reset_mock()

        filter_set_name = 'unknown'
        feedbacks.get_feedbacks_total_count(filter_set_name, active_filters, org_list)
        mock_get_approval_counts.assert_not_called()
        mock_get_type_counts.assert_not_called()
        mock_get_organization_counts.assert_not_called()
