import pytest
from ckan import model
from ckan.model.user import User
from ckan.tests import factories

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
    get_engine,
)
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentCategory,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.services.resource.comment import (
    approve_resource_comment,
    create_reply,
    create_resource_comment,
    get_comment_reply,
    get_cookie,
    get_resource,
    get_resource_comment_categories,
    get_resource_comments,
)


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestComments:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = get_engine('db', '5432', 'ckan_test', 'ckan', 'ckan')
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_resource(self):
        resource = factories.Resource()
        assert type(get_resource(resource['id'])) is model.resource.Resource

    def test_get_resource_comments(self):
        assert not get_resource_comments()
        resource = factories.Resource()
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        session.commit()
        assert get_resource_comments()
        assert get_resource_comments(resource['id'])
        assert not get_resource_comments('test')
        assert not get_resource_comments(resource['id'], True)

    def test_create_resource_comment(self):
        pass

    def test_get_resource_comment_categories(self):
        assert get_resource_comment_categories() == ResourceCommentCategory

    def test_approve_resource_comment(self):
        resource = factories.Resource()
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        session.commit()
        comment_id = session.query(ResourceComment).first().id
        user_id = session.query(User).first().id

        assert not get_resource_comments(resource['id'])[0].approval

        approve_resource_comment(comment_id, user_id)
        session.commit()
        assert get_resource_comments(resource['id'])[0].approval

    def test_get_comment_reply(self):
        pass

    def test_create_reply(self):
        resource = factories.Resource()
        category = get_resource_comment_categories().REQUEST
        create_resource_comment(resource['id'], category, 'test', 1)
        comment_id = session.query(ResourceComment).first().id
        user_id = session.query(User).first().id
        assert not get_comment_reply(comment_id)
        create_reply(comment_id, 'test_reply', user_id)
        session.commit()
        assert get_comment_reply(comment_id)

    def test_get_cookie(self):
        resource = factories.Resource()
        assert not get_cookie(resource['id'])
