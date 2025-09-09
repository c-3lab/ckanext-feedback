import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from ckan import model
from ckan.tests import factories
from ckan.tests.helpers import reset_db
from flask import g

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


@pytest.fixture(scope='function')
def flask_context():
    from ckan.tests.helpers import _get_test_app

    app = _get_test_app()
    with app.flask_app.test_request_context('/'):
        yield app.flask_app


def _setup_flask_context_with_user(flask_context, user_dict):
    from ckan.lib.app_globals import app_globals

    app_globals._check_uptodate = lambda: None

    with patch('flask_login.utils._get_user') as current_user:
        user_obj = model.User.get(user_dict['name'])
        current_user.return_value = user_obj
        g.userobj = current_user

        # Setup babel
        with patch('ckan.lib.i18n.get_lang') as mock_get_lang:
            mock_get_lang.return_value = 'en'
            yield current_user


@pytest.fixture(scope='function')
def admin_context(flask_context, sysadmin):
    yield from _setup_flask_context_with_user(flask_context, sysadmin)


@pytest.fixture(scope='function')
def user_context(flask_context, user):
    yield from _setup_flask_context_with_user(flask_context, user)


@pytest.fixture(scope='function')
def utilization_with_params(resource):
    def _create_utilization(
        title='test_title',
        description='test_description',
        approval=True,
        approval_user_id=None,
        url='test_url',
    ):
        utilization = Utilization(
            id=str(uuid.uuid4()),
            resource_id=resource['id'],
            title=title,
            url=url,
            description=description,
            comment=0,
            approval=approval,
            approved=datetime(2024, 1, 1, 15, 0, 0) if approval else None,
            approval_user_id=approval_user_id,
        )
        session.add(utilization)
        session.flush()
        return utilization

    return _create_utilization


@pytest.fixture(scope='function')
def utilization_comment_with_params(utilization):
    def _create_comment(
        category=UtilizationCommentCategory.REQUEST,
        content='test_content',
        approval=True,
        approval_user_id=None,
    ):
        comment = UtilizationComment(
            id=str(uuid.uuid4()),
            utilization_id=utilization.id,
            category=category,
            content=content,
            created=datetime(2024, 1, 1, 15, 0, 0),
            approval=approval,
            approved=datetime(2024, 1, 1, 15, 0, 0) if approval else None,
            approval_user_id=approval_user_id,
            attached_image_filename='test_attached_image.jpg',
        )
        session.add(comment)
        session.flush()
        return comment

    return _create_comment


@pytest.fixture(scope='function')
def multiple_utilizations(resource):
    def _create_multiple(count=2, approval=True):
        utilizations = []
        for i in range(count):
            utilization = Utilization(
                id=str(uuid.uuid4()),
                resource_id=resource['id'],
                title=f'test_title_{i}',
                url=f'test_url_{i}',
                description=f'test_description_{i}',
                comment=0,
                approval=approval,
                approved=datetime(2024, 1, 1, 15, 0, 0) if approval else None,
            )
            session.add(utilization)
            session.flush()
            utilizations.append(utilization)
        return utilizations

    return _create_multiple


@pytest.fixture(scope='function')
def utilization_with_comment(resource, user):
    def _create_with_comment(
        title='test_title',
        description='test_description',
        comment_content='test_comment',
        approval=True,
    ):
        utilization = Utilization(
            id=str(uuid.uuid4()),
            resource_id=resource['id'],
            title=title,
            url='test_url',
            description=description,
            comment=1,
            approval=approval,
            approved=datetime(2024, 1, 1, 15, 0, 0) if approval else None,
            approval_user_id=user['id'] if approval else None,
        )
        session.add(utilization)
        session.flush()

        comment = UtilizationComment(
            id=str(uuid.uuid4()),
            utilization_id=utilization.id,
            category=UtilizationCommentCategory.REQUEST,
            content=comment_content,
            created=datetime(2024, 1, 1, 15, 0, 0),
            approval=approval,
            approved=datetime(2024, 1, 1, 15, 0, 0) if approval else None,
            approval_user_id=user['id'] if approval else None,
        )
        session.add(comment)
        session.flush()

        return utilization, comment

    return _create_with_comment
