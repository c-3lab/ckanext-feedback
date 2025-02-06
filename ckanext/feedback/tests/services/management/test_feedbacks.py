import logging
import uuid
from datetime import datetime

import pytest
from ckan import model
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentCategory,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.services.management import feedbacks

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


engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestFeedbacks:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_feedbacks(self):
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=dataset['id'])

        comment_id = str(uuid.uuid4())
        category = ResourceCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()
        approved = datetime.now()

        register_resource_comment(
            comment_id,
            resource['id'],
            category,
            content,
            None,
            created,
            False,
            approved,
            None,
        )

        session.commit()

        feedback_list, total_count = feedbacks.get_feedbacks()

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

        assert feedback_list == expected_feedback_list
        assert total_count == 1

        owner_orgs = [organization['id']]
        active_filters = [
            'approved',
            'unapproved',
            'resource',
            'utilization',
            'util-comment',
            organization['name'],
        ]
        sort = 'newest'
        limit = 20
        offset = 0

        feedback_list, total_count = feedbacks.get_feedbacks(
            owner_orgs, active_filters, sort, limit, offset
        )

        assert feedback_list == expected_feedback_list
        assert total_count == 1

        owner_orgs = None
        active_filters = []
        sort = 'oldest'

        feedback_list, total_count = feedbacks.get_feedbacks(
            owner_orgs, active_filters, sort, limit, offset
        )

        assert feedback_list == expected_feedback_list
        assert total_count == 1

        sort = 'dataset_asc'

        feedback_list, total_count = feedbacks.get_feedbacks(
            owner_orgs, active_filters, sort, limit, offset
        )

        assert feedback_list == expected_feedback_list
        assert total_count == 1

        sort = 'dataset_desc'

        feedback_list, total_count = feedbacks.get_feedbacks(
            owner_orgs, active_filters, sort, limit, offset
        )

        assert feedback_list == expected_feedback_list
        assert total_count == 1

        sort = 'resource_asc'

        feedback_list, total_count = feedbacks.get_feedbacks(
            owner_orgs, active_filters, sort, limit, offset
        )

        assert feedback_list == expected_feedback_list
        assert total_count == 1

        sort = 'resource_desc'

        feedback_list, total_count = feedbacks.get_feedbacks(
            owner_orgs, active_filters, sort, limit, offset
        )

        assert feedback_list == expected_feedback_list
        assert total_count == 1

        sort = ''

        feedback_list, total_count = feedbacks.get_feedbacks(
            owner_orgs, active_filters, sort, limit, offset
        )

        assert feedback_list == expected_feedback_list
        assert total_count == 1

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_feedbacks_count(self):
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=dataset['id'])

        comment_id = str(uuid.uuid4())
        category = ResourceCommentCategory.QUESTION
        content = 'test content'
        created = datetime.now()
        approved = datetime.now()

        register_resource_comment(
            comment_id,
            resource['id'],
            category,
            content,
            None,
            created,
            False,
            approved,
            None,
        )

        session.commit()

        owner_orgs = [organization['id']]
        active_filters = 'unapproved'

        total_count = feedbacks.get_feedbacks_count(owner_orgs, active_filters)

        assert total_count == 1
