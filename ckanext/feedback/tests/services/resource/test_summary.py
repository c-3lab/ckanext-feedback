import pytest
from ckan.model import User

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


@pytest.mark.db_test
class TestSummary:
    def test_get_package_comments(self, resource, resource_comment):
        result = get_package_comments(resource['package_id'])
        assert result == 1

    def test_get_resource_comments(self, resource, resource_comment):
        result = get_resource_comments(resource['id'])
        assert result == 1

    def test_get_package_rating(self, resource, resource_comment):
        result = get_package_rating(resource['package_id'])
        assert result == resource_comment.rating

    def test_get_package_rating_with_no_comments(self, resource):
        result = get_package_rating(resource['package_id'])
        assert result == 0

    def test_get_resource_rating(self, resource, resource_comment):
        result = get_resource_rating(resource['id'])
        assert result == resource_comment.rating

    def test_create_resource_summary(self, resource):
        create_resource_summary(resource['id'])
        query = session.query(ResourceCommentSummary).all()
        assert len(query) == 1

    def test_refresh_resource_summary(self, resource):
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
        session.flush()
        refresh_resource_summary(resource['id'])
        session.commit()
        session.expire_all()

        summary = session.query(ResourceCommentSummary).first()
        assert summary.comment == 1
        assert summary.rating == 3.0
        assert summary.updated

        create_resource_comment(resource['id'], category, 'test2', 5)
        session.commit()
        comment_id = session.query(ResourceComment).all()[1].id
        approve_resource_comment(comment_id, user_id)
        session.flush()
        refresh_resource_summary(resource['id'])
        session.commit()
        session.expire_all()

        summary = session.query(ResourceCommentSummary).first()
        assert summary.comment == 2
        assert summary.rating == 4.0
        assert summary.updated
