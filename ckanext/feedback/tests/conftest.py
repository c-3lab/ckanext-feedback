import uuid

import pytest
from ckan.tests import factories

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentCategory,
    ResourceCommentReactions,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.types import ResourceCommentResponseStatus


@pytest.fixture(autouse=True)
def reset_transaction():
    yield
    session.rollback()


@pytest.fixture(scope="function")
def user():
    return factories.User()


@pytest.fixture(scope="function")
def sysadmin():
    return factories.Sysadmin()


@pytest.fixture(scope="function")
def organization():
    return factories.Organization()


@pytest.fixture(scope="function")
def dataset(organization):
    return factories.Dataset(owner_org=organization['id'])


@pytest.fixture(scope="function")
def resource(dataset):
    return factories.Resource(package_id=dataset['id'])


@pytest.fixture(scope='function')
def resource_comment(resource):
    comment = ResourceComment(
        id=str(uuid.uuid4()),
        resource_id=resource['id'],
        category=ResourceCommentCategory.REQUEST,
        content='test_content',
        rating=3,
        attached_image_filename='test_image.jpg',
    )
    session.add(comment)
    session.flush()
    return comment


@pytest.fixture(scope='function')
def resource_comment_reactions(user, resource_comment):
    reactions = ResourceCommentReactions(
        id=str(uuid.uuid4()),
        resource_comment_id=resource_comment.id,
        response_status=ResourceCommentResponseStatus.STATUS_NONE,
        admin_liked=False,
    )
    session.add(reactions)
    session.flush()
    return reactions
