import pytest
from ckan import model
from ckan.tests import factories
from ckan.model.user import User

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
    get_engine,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.services.resource.summary import (
    get_package_comments,
    get_resource_comments,
    get_package_rating,
    get_resource_rating,
    create_resource_summary,
    refresh_resource_summary,
)
from ckanext.feedback.services.resource.comment import (
    get_resource_comment_categories,
    create_resource_comment,
    approve_resource_comment,
)
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentSummary,
)

@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestResourceServices:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = get_engine('db', '5432', 'ckan_test', 'ckan', 'ckan')
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_package_comments(self):
        resource = factories.Resource()
        assert get_package_comments(resource['package_id']) == 0
        resource_comment_summary = ResourceCommentSummary(
            id=str('test_id'),
            resource_id=resource['id'],
            comment=1,
            rating=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(resource_comment_summary)
        assert get_package_comments(resource['package_id']) == 1

    def test_get_resource_comments(self):
        resource = factories.Resource()
        assert get_resource_comments(resource['id']) == 0
        resource_comment_summary = ResourceCommentSummary(
            id=str('test_id'),
            resource_id=resource['id'],
            comment=1,
            rating=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(resource_comment_summary)
        assert get_resource_comments(resource['id']) == 1

    def test_get_package_rating(self):
        resource = factories.Resource()
        assert get_package_rating(resource['package_id']) == 0
        resource_comment_summary = ResourceCommentSummary(
            id=str('test_id'),
            resource_id=resource['id'],
            comment=1,
            rating=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(resource_comment_summary)
        assert get_package_rating(resource['package_id']) == 1

    def test_get_resource_rating(self):
        resource = factories.Resource()
        assert get_resource_rating(resource['id']) == 0
        resource_comment_summary = ResourceCommentSummary(
            id=str('test_id'),
            resource_id=resource['id'],
            comment=1,
            rating=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(resource_comment_summary)
        assert get_resource_rating(resource['id']) == 1

    def test_create_resource_summary(self):
        query = session.query(ResourceCommentSummary).all()
        assert len(query) == 0

        resource = factories.Resource()
        create_resource_summary(resource['id'])
        query = session.query(ResourceCommentSummary).all()
        assert len(query) == 1

    def test_refresh_resource_summary(self):
        resource = factories.Resource()
        create_resource_summary(resource['id'])

        summary = (
            session.query(ResourceCommentSummary)
            .first()
        )
        assert summary.comment == 0
        assert summary.rating == 0
        assert not summary.updated

        create_resource_comment(resource['id'], get_resource_comment_categories().REQUEST, "test", 3)
        comment_id = session.query(ResourceComment).first().id
        user_id = session.query(User).first().id
        approve_resource_comment(comment_id, user_id)
        refresh_resource_summary(resource['id'])

        summary = (
            session.query(ResourceCommentSummary)
            .first()
        )
        assert summary.comment == 1
        assert summary.rating == 3.0
        assert summary.updated

        create_resource_comment(resource['id'], get_resource_comment_categories().REQUEST, "test2", 5)
        comment_id = session.query(ResourceComment).order_by(ResourceComment.id.desc()).first().id
        approve_resource_comment(comment_id, user_id)
        refresh_resource_summary(resource['id'])

        summary = (
            session.query(ResourceCommentSummary)
            .first()
        )
        assert summary.comment == 2
        assert summary.rating == 4.0
        assert summary.updated
