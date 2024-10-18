import pytest
from ckan import model
from ckan.model.user import User
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentSummary,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.services.resource.comment import (
    approve_resource_comment,
    create_resource_comment,
    get_resource_comment_categories,
)
from ckanext.feedback.services.resource.summary import (
    create_resource_summary,
    get_package_comments,
    get_package_rating,
    get_resource_comments,
    get_resource_rating,
    refresh_resource_summary,
)


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestResourceServices:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = model.meta.engine
        create_resource_like_tables(engine)
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
        session.commit()
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
        session.commit()
        assert get_resource_comments(resource['id']) == 1

    def test_get_package_rating(self):
        resource = factories.Resource()
        assert get_package_rating(resource['package_id']) == 0
        resource_comment_summary = ResourceCommentSummary(
            id=str('test_id'),
            resource_id=resource['id'],
            comment=1,
            rating=1,
            rating_comment=1,
            created='2023-03-31 01:23:45.123456',
            updated='2023-03-31 01:23:45.123456',
        )
        session.add(resource_comment_summary)
        session.commit()
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
        session.commit()
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
        refresh_resource_summary(resource['id'])
        create_resource_summary(resource['id'])
        session.commit()
        summary = session.query(ResourceCommentSummary).first()
        assert summary.comment == 0
        assert summary.rating == 0
        assert not summary.updated
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 3)
        session.commit()
        comment_id = session.query(ResourceComment).first().id
        user_id = session.query(User).first().id
        approve_resource_comment(comment_id, user_id)
        refresh_resource_summary(resource['id'])
        session.commit()

        summary = session.query(ResourceCommentSummary).first()
        assert summary.comment == 1
        assert summary.rating == 3.0
        assert summary.updated

        create_resource_comment(resource['id'], category, 'test2', 5)
        session.commit()
        comment_id = session.query(ResourceComment).all()[1].id
        approve_resource_comment(comment_id, user_id)
        refresh_resource_summary(resource['id'])
        session.commit()

        summary = session.query(ResourceCommentSummary).first()
        assert summary.comment == 2
        assert summary.rating == 4.0
        assert summary.updated
