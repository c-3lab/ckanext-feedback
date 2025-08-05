import uuid
from datetime import datetime

import pytest
from ckan import model
from ckan.tests import factories
from ckan.tests.helpers import reset_db

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.models.likes import ResourceLike, ResourceLikeMonthly
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentCategory,
    ResourceCommentReactions,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.types import ResourceCommentResponseStatus
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
)


@pytest.fixture(autouse=True)
def reset_transaction(request):
    if request.node.get_closest_marker('db_test'):
        reset_db()

        model.repo.init_db()
        engine = model.meta.engine
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

        yield

        session.rollback()
        reset_db()
    else:
        yield


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
        attached_image_filename='test_attached_image.jpg',
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


@pytest.fixture(scope='function')
def utilization(user, resource):
    utilization = Utilization(
        id=str(uuid.uuid4()),
        resource_id=resource['id'],
        title='test_title',
        url='test_url',
        description='test_description',
        comment=0,
        created=datetime(2024, 1, 1, 15, 0, 0),
        approval=True,
        approved=datetime(2024, 1, 1, 15, 0, 0),
        approval_user_id=user['id'],
    )
    session.add(utilization)
    session.flush()
    return utilization


@pytest.fixture(scope='function')
def utilization_comment(user, utilization):
    comment = UtilizationComment(
        id=str(uuid.uuid4()),
        utilization_id=utilization.id,
        category=UtilizationCommentCategory.REQUEST,
        content='test_content',
        created=datetime(2024, 1, 1, 15, 0, 0),
        approval=True,
        approved=datetime(2024, 1, 1, 15, 0, 0),
        approval_user_id=user['id'],
        attached_image_filename='test_attached_image.jpg',
    )
    session.add(comment)
    session.flush()
    return comment


@pytest.fixture(scope='function')
def download_summary(resource):
    download_summary = DownloadSummary(
        id=str(uuid.uuid4()),
        resource_id=resource['id'],
        download=1,
        created=datetime(2024, 1, 1, 15, 0, 0),
        updated=datetime(2024, 1, 1, 15, 0, 0),
    )
    session.add(download_summary)
    session.flush()
    return download_summary


@pytest.fixture(scope='function')
def resource_like(resource):
    resource_like = ResourceLike(
        id=str(uuid.uuid4()),
        resource_id=resource['id'],
        like_count=1,
        created=datetime(2024, 1, 1, 15, 0, 0),
        updated=datetime(2024, 1, 1, 15, 0, 0),
    )
    session.add(resource_like)
    session.flush()
    return resource_like


@pytest.fixture(scope='function')
def resource_like_monthly(resource):
    resource_like_monthly = ResourceLikeMonthly(
        id=str(uuid.uuid4()),
        resource_id=resource['id'],
        like_count=1,
        created=datetime(2024, 1, 1, 15, 0, 0),
        updated=datetime(2024, 1, 1, 15, 0, 0),
    )
    session.add(resource_like_monthly)
    session.flush()
    return resource_like_monthly
