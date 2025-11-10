import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

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
    ResourceCommentMoralCheckLog,
    ResourceCommentReactions,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.types import (
    MoralCheckAction,
    ResourceCommentResponseStatus,
)
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
    UtilizationCommentMoralCheckLog,
)
from ckanext.feedback.services.resource.summary import refresh_resource_summary


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


@pytest.fixture(scope='function')
def sysadmin_env():
    user = factories.SysadminWithToken()
    env = {'Authorization': user['token']}
    return env


@pytest.fixture(scope='function')
def user_env():
    user = factories.UserWithToken()
    env = {'Authorization': user['token']}
    return env


@pytest.fixture(scope="function")
def organization():
    return factories.Organization()


@pytest.fixture(scope="function")
def another_organization():
    return factories.Organization()


@pytest.fixture(scope="function")
def dataset(organization):
    return factories.Dataset(owner_org=organization['id'])


@pytest.fixture(scope="function")
def resource(dataset):
    return factories.Resource(package_id=dataset['id'])


@pytest.fixture(scope="function")
def api_token(user):
    return factories.APIToken(user_id=user['id'])


@pytest.fixture(scope='function')
def resource_comment(resource):
    comment = ResourceComment(
        id=str(uuid.uuid4()),
        resource_id=resource['id'],
        category=ResourceCommentCategory.REQUEST,
        content='test_content',
        rating=3,
        approval=True,
        attached_image_filename='test_attached_image.jpg',
    )
    session.add(comment)
    session.commit()
    refresh_resource_summary(resource['id'])
    session.commit()
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


@pytest.fixture(scope='function')
def mock_resource_object():
    def _create_mock_resource(org_id='mock_org_id', org_name='mock_organization_name'):
        mock_resource = MagicMock()
        mock_resource.Resource = MagicMock()
        mock_resource.Resource.id = 'mock_resource_id'
        mock_resource.Resource.name = 'mock_resource_name'
        mock_resource.Resource.package = MagicMock()
        mock_resource.Resource.package.id = 'mock_package_id'
        mock_resource.Resource.package.owner_org = org_id
        mock_resource.organization_id = org_id
        mock_resource.organization_name = org_name
        return mock_resource

    return _create_mock_resource


@pytest.fixture(scope='function')
def mock_utilization_object():
    def _create_mock_utilization(
        resource_id='mock_resource_id',
        owner_org='mock_org_id',
        package_id='mock_package_id',
    ):
        mock_utilization = MagicMock()
        mock_utilization.id = 'mock_utilization_id'
        mock_utilization.resource_id = resource_id
        mock_utilization.owner_org = owner_org
        mock_utilization.package_id = package_id
        mock_utilization.title = 'mock_title'
        mock_utilization.url = 'mock_url'
        mock_utilization.description = 'mock_description'
        return mock_utilization

    return _create_mock_utilization


@pytest.fixture(scope='function')
def mock_current_user_fixture():
    def _mock_current_user(current_user, user):
        user_obj = model.User.get(user['name'])
        current_user.return_value = user_obj
        g.userobj = current_user

    return _mock_current_user
    #     user_obj = model.User.get(user['name'])
    #     # mock current_user
    #     current_user.return_value = user_obj

    # return _mock_current_user


@pytest.fixture(scope='function')
def resource_comment_moral_check_log(resource):
    moral_check_log = ResourceCommentMoralCheckLog(
        id=str(uuid.uuid4()),
        resource_id=resource['id'],
        action=MoralCheckAction.INPUT_SELECTED,
        input_comment='test_input_comment',
        suggested_comment='test_suggested_comment',
        output_comment='test_output_comment',
        timestamp=datetime(2024, 1, 1, 15, 0, 0),
    )
    session.add(moral_check_log)
    session.flush()
    return moral_check_log


@pytest.fixture(scope='function')
def utilization_comment_moral_check_log(utilization):
    moral_check_log = UtilizationCommentMoralCheckLog(
        id=str(uuid.uuid4()),
        utilization_id=utilization.id,
        action=MoralCheckAction.INPUT_SELECTED,
        input_comment='test_input_comment',
        suggested_comment='test_suggested_comment',
        output_comment='test_output_comment',
        timestamp=datetime(2024, 1, 1, 15, 0, 0),
    )
    session.add(moral_check_log)
    session.flush()
    return moral_check_log
