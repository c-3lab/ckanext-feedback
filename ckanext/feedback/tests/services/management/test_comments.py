import uuid
from datetime import datetime
from unittest.mock import patch

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
    ResourceCommentSummary,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
)
from ckanext.feedback.services.management import comments
from ckanext.feedback.services.resource import comment, summary


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


def get_resource_comment_summary(resource_id):
    resource_comment_summary = (
        session.query(ResourceCommentSummary)
        .filter(ResourceCommentSummary.resource_id == resource_id)
        .first()
    )
    return resource_comment_summary


engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestComments:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

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

        assert comments.get_utilization_comments(id) == 0

        register_utilization(id, resource['id'], title, description, True)
        register_utilization_comment(
            comment_id, id, category, content, created, True, approved, None
        )
        session.commit()

        assert comments.get_utilization_comments(id) == 1

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

        assert len(comments.get_utilizations([comment_id, another_comment_id])) == 2
        assert (
            comments.get_utilizations([comment_id, another_comment_id])[0].id
            == utilization_id
        )
        assert (
            comments.get_utilizations([comment_id, another_comment_id])[1].id
            == another_utilization_id
        )

    def test_get_organization(self):
        organization_dict = factories.Organization()
        assert (
            comments.get_organization(organization_dict['id']).id
            == organization_dict['id']
        )

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch('ckanext.feedback.services.management.comments.get_utilization_comments')
    @patch('ckanext.feedback.services.management.comments.session.bulk_update_mappings')
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
        comments.refresh_utilizations_comments(
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

        resource_comment_summaries = comments.get_resource_comment_summaries(
            comment_id_list
        )

        assert len(resource_comment_summaries) == 2
        assert resource_comment_summaries[0].comment == 1
        assert resource_comment_summaries[1].comment == 1

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch('ckanext.feedback.services.management.comments.session.bulk_update_mappings')
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

        comments.refresh_resources_comments(resource_comment_summaries)

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

        comments.delete_resource_comments(
            [resource_comment[0].id, another_resource_comment[0].id]
        )
        comments.refresh_resources_comments(resource_comment_summaries)
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

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch('ckanext.feedback.services.management.comments.session.bulk_update_mappings')
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

        comments.approve_utilization_comments(comment_id_list, None)

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

        comments.delete_utilization_comments([comment_id])

        utilization_comment = get_registered_utilization_comment(utilization_id)
        assert len(utilization_comment) == 0

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    @patch('ckanext.feedback.services.management.comments.session.bulk_update_mappings')
    def test_approve_resource_comments(self, mock_mappings):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        category = ResourceCommentCategory.QUESTION

        comment.create_resource_comment(resource['id'], category, 'test content 1', 1)
        resource_comment = comment.get_resource_comments(resource['id'], None)

        session.commit()

        comment_id_list = [resource_comment[0].id]

        comments.approve_resource_comments(comment_id_list, None)

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

        comments.delete_resource_comments(comment_id_list)

        resource_comment = comment.get_resource_comments(resource['id'], None)
        assert len(resource_comment) == 0
