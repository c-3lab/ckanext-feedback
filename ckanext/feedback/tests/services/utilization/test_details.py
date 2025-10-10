import uuid
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import ckan.tests.factories as factories
import pytest
from ckan import model
from ckan.model.package import Package
from ckan.model.resource import Resource

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.issue import IssueResolution
from ckanext.feedback.models.session import session
from ckanext.feedback.models.types import MoralCheckAction
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
)
from ckanext.feedback.services.utilization.details import (
    approve_utilization,
    approve_utilization_comment,
    create_issue_resolution,
    create_utilization_comment,
    create_utilization_comment_moral_check_log,
    get_attached_image_path,
    get_comment_attached_image_files,
    get_issue_resolutions,
    get_resource_by_utilization_id,
    get_upload_destination,
    get_utilization,
    get_utilization_comment,
    get_utilization_comment_categories,
    get_utilization_comment_moral_check_logs,
    get_utilization_comments,
    refresh_utilization_comments,
)


def get_registered_utilization(resource_id):
    return (
        session.query(
            Utilization.id,
            Utilization.approval,
            Utilization.approved,
            Utilization.approval_user_id,
        )
        .filter(Utilization.resource_id == resource_id)
        .first()
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


def get_registered_issue_resolution(utilization_id):
    return (
        session.query(
            IssueResolution.utilization_id,
            IssueResolution.description,
            IssueResolution.creator_user_id,
        )
        .filter(IssueResolution.utilization_id == utilization_id)
        .first()
    )


def register_utilization(id, resource_id, title, url, description, approval):
    utilization = Utilization(
        id=id,
        resource_id=resource_id,
        title=title,
        url=url,
        description=description,
        approval=approval,
    )
    session.add(utilization)
    session.commit()


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
    session.commit()


def convert_utilization_comment_to_tuple(utilization_comment):
    return (
        utilization_comment.id,
        utilization_comment.utilization_id,
        utilization_comment.category,
        utilization_comment.content,
        utilization_comment.created,
        utilization_comment.approval,
        utilization_comment.approved,
        utilization_comment.approval_user_id,
    )


engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestUtilizationDetailsService:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_utilization(self):
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=dataset['id'])

        assert get_registered_utilization(resource['id']) is None

        id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(id, resource['id'], title, url, description, False)

        result = get_utilization(id)
        expected_utilization = (
            title,
            url,
            description,
            0,
            False,
            resource['name'],
            resource['id'],
            dataset['title'],
            dataset['name'],
            organization['id'],
        )
        assert result == expected_utilization

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_approve_utilization(self):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])
        test_datetime = datetime.now()

        id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(id, resource['id'], title, url, description, False)

        result = get_registered_utilization(resource['id'])
        unapproved_utilization = (id, False, None, None)
        assert result == unapproved_utilization

        approve_utilization(id, user['id'])

        result = get_registered_utilization(resource['id'])
        approved_utilization = (id, True, test_datetime, user['id'])
        assert result == approved_utilization

    @patch('ckanext.feedback.services.utilization.details.session')
    def test_get_utilization_comment(self, mock_session):
        comment_id = 'comment_id'
        utilization_id = 'utilization_id'
        approval = True
        attached_image_filename = 'attached_image_filename'
        owner_orgs = ['org1', 'org2']

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.first.return_value = 'mock_comment'
        mock_session.query.return_value = mock_query

        get_utilization_comment(
            comment_id, utilization_id, approval, attached_image_filename, owner_orgs
        )

        mock_session.query.assert_called_once_with(UtilizationComment)
        assert mock_query.filter.call_count == 5
        mock_query.join.assert_has_calls(
            [
                call(Resource),
                call(Package),
            ]
        )
        mock_query.first.assert_called_once()

    @patch('ckanext.feedback.services.utilization.details.session')
    def test_get_utilization_comment_with_none_args(self, mock_session):
        comment_id = 'comment_id'

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.first.return_value = 'mock_comment'
        mock_session.query.return_value = mock_query

        get_utilization_comment(comment_id)

        mock_session.query.assert_called_once_with(UtilizationComment)
        assert mock_query.filter.call_count == 1
        mock_query.join.assert_not_called()
        mock_query.first.assert_called_once()

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilization_comments_utilization_id_and_approval_are_None(self):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(
            utilization_id, resource['id'], title, url, description, False
        )
        utilization = get_registered_utilization(resource['id'])

        created = datetime.now()
        approved = datetime.now()
        unapproved_comment_id = str(uuid.uuid4())
        category_request = UtilizationCommentCategory.REQUEST
        unapproved_content = 'unapproved content'
        register_utilization_comment(
            unapproved_comment_id,
            utilization.id,
            category_request,
            unapproved_content,
            created,
            False,
            None,
            None,
        )
        comments = get_utilization_comments(utilization.id, None)

        assert len(comments) == 1
        comment = convert_utilization_comment_to_tuple(comments[0])
        unapproved_comment = (
            unapproved_comment_id,
            utilization.id,
            category_request,
            unapproved_content,
            created,
            False,
            None,
            None,
        )
        assert comment == unapproved_comment

        approved_comment_id = str(uuid.uuid4())
        category_thank = UtilizationCommentCategory.THANK
        approved_content = 'approved content'
        register_utilization_comment(
            approved_comment_id,
            utilization.id,
            category_thank,
            approved_content,
            datetime(2001, 1, 2, 3, 4),
            True,
            approved,
            user['id'],
        )
        comments = get_utilization_comments(None, None)

        assert len(comments) == 2
        approved_result = convert_utilization_comment_to_tuple(comments[0])
        unapproved_result = convert_utilization_comment_to_tuple(comments[1])
        approved_comment = (
            approved_comment_id,
            utilization.id,
            category_thank,
            approved_content,
            datetime(2001, 1, 2, 3, 4),
            True,
            approved,
            user['id'],
        )
        assert unapproved_result == unapproved_comment
        assert approved_result == approved_comment

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilization_comments_approval_is_False(self):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(
            utilization_id, resource['id'], title, url, description, False
        )
        utilization = get_registered_utilization(resource['id'])

        created = datetime.now()
        approved = datetime.now()
        unapproved_comment_id = str(uuid.uuid4())
        approved_comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'

        register_utilization_comment(
            unapproved_comment_id,
            utilization.id,
            category,
            content,
            created,
            False,
            None,
            None,
        )
        register_utilization_comment(
            approved_comment_id,
            utilization.id,
            category,
            content,
            created,
            True,
            approved,
            user['id'],
        )
        comments = get_utilization_comments(utilization.id, False)

        assert len(comments) == 1
        unapproved_comment = convert_utilization_comment_to_tuple(comments[0])
        expect_unapproved_comment = (
            unapproved_comment_id,
            utilization.id,
            category,
            content,
            created,
            False,
            None,
            None,
        )
        assert unapproved_comment == expect_unapproved_comment

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilization_comments_approval_is_True(self):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(
            utilization_id, resource['id'], title, url, description, False
        )
        utilization = get_registered_utilization(resource['id'])

        created = datetime.now()
        approved = datetime.now()
        unapproved_comment_id = str(uuid.uuid4())
        approved_comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'

        register_utilization_comment(
            unapproved_comment_id,
            utilization.id,
            category,
            content,
            created,
            False,
            None,
            None,
        )
        register_utilization_comment(
            approved_comment_id,
            utilization.id,
            category,
            content,
            created,
            True,
            approved,
            user['id'],
        )
        comments = get_utilization_comments(utilization.id, True)

        assert len(comments) == 1
        approved_comment = convert_utilization_comment_to_tuple(comments[0])
        fake_utilization_comment_approved = (
            approved_comment_id,
            utilization.id,
            category,
            content,
            created,
            True,
            approved,
            user['id'],
        )
        assert approved_comment == fake_utilization_comment_approved

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilization_comments_owner_org(self):
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(
            utilization_id, resource['id'], title, url, description, False
        )
        utilization = get_registered_utilization(resource['id'])

        created = datetime.now()
        approved = datetime.now()
        unapproved_comment_id = str(uuid.uuid4())
        approved_comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'

        register_utilization_comment(
            unapproved_comment_id,
            utilization.id,
            category,
            content,
            created,
            False,
            None,
            None,
        )
        register_utilization_comment(
            approved_comment_id,
            utilization.id,
            category,
            content,
            created,
            True,
            approved,
            user['id'],
        )
        comments = get_utilization_comments(utilization.id, True, [organization['id']])

        assert len(comments) == 1
        approved_comment = convert_utilization_comment_to_tuple(comments[0])
        fake_utilization_comment_approved = (
            approved_comment_id,
            utilization.id,
            category,
            content,
            created,
            True,
            approved,
            user['id'],
        )
        assert approved_comment == fake_utilization_comment_approved

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilization_comments_limit_offset(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(
            utilization_id, resource['id'], title, url, description, False
        )
        utilization = get_registered_utilization(resource['id'])
        limit = 20
        offset = 0

        created = datetime.now()
        unapproved_comment_id = str(uuid.uuid4())
        category_request = UtilizationCommentCategory.REQUEST
        unapproved_content = 'unapproved content'
        register_utilization_comment(
            unapproved_comment_id,
            utilization.id,
            category_request,
            unapproved_content,
            created,
            False,
            None,
            None,
        )
        comments, total_count = get_utilization_comments(
            utilization.id,
            None,
            limit=limit,
            offset=offset,
        )

        assert len(comments) == 1
        comment = convert_utilization_comment_to_tuple(comments[0])
        unapproved_comment = (
            unapproved_comment_id,
            utilization.id,
            category_request,
            unapproved_content,
            created,
            False,
            None,
            None,
        )
        assert comment == unapproved_comment

    def test_create_utilization_comment(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(
            utilization_id, resource['id'], title, url, description, False
        )
        utilization = get_registered_utilization(resource['id'])

        category = UtilizationCommentCategory.REQUEST
        content = 'test content'
        create_utilization_comment(utilization.id, category, content)

        comments = get_registered_utilization_comment(utilization.id)
        comment = comments[0]
        assert comment.utilization_id == utilization.id
        assert comment.category == category
        assert comment.content == content
        assert comment.approval is False
        assert comment.approved is None
        assert comment.approval_user_id is None

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_approve_utilization_comment(self):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'
        register_utilization(
            utilization_id, resource['id'], title, url, description, False
        )
        utilization = get_registered_utilization(resource['id'])

        created = datetime.now()
        comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'
        register_utilization_comment(
            comment_id,
            utilization.id,
            category,
            content,
            created,
            False,
            None,
            None,
        )

        approve_utilization_comment(comment_id, user['id'])
        approved_comment = get_registered_utilization_comment(utilization.id)[0]

        assert approved_comment.category == category
        assert approved_comment.content == content
        assert approved_comment.approval is True
        assert approved_comment.approved == datetime.now()
        assert approved_comment.approval_user_id == user['id']

    def test_get_utilization_comment_categories(self):
        assert get_utilization_comment_categories() == UtilizationCommentCategory

    def test_get_issue_resolutions(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        user = factories.User()

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        utilization_description = 'test description'

        register_utilization(
            utilization_id, resource['id'], title, url, utilization_description, False
        )

        utilization = get_registered_utilization(resource['id'])
        assert get_registered_issue_resolution(utilization.id) is None
        issue_resolution_description = 'test issue resolution description'
        time = datetime.now()

        session.add(
            IssueResolution(
                utilization_id=utilization.id,
                description=issue_resolution_description,
                created=time,
                creator_user_id=user['id'],
            )
        )
        session.commit()

        issue_resolution = get_issue_resolutions(utilization.id)[0]

        assert issue_resolution.utilization_id == utilization.id
        assert issue_resolution.description == issue_resolution_description
        assert issue_resolution.created == time
        assert issue_resolution.creator_user_id == user['id']

    def test_create_issue_resolution(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        user = factories.Sysadmin()

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        utilization_description = 'test description'

        register_utilization(
            utilization_id, resource['id'], title, url, utilization_description, False
        )

        utilization = get_registered_utilization(resource['id'])
        issue_resolution_description = 'test_issue_resolution_description'
        create_issue_resolution(
            utilization.id, issue_resolution_description, user['id']
        )

        issue_resolution = (utilization.id, issue_resolution_description, user['id'])

        result = get_registered_issue_resolution(utilization.id)

        assert result == issue_resolution

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_refresh_utilization_comments(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        user = factories.Sysadmin()

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        url = 'test url'
        description = 'test description'

        created = datetime.now()
        approved = datetime.now()
        comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'

        register_utilization(
            utilization_id, resource['id'], title, url, description, True
        )

        result = get_utilization(utilization_id)

        assert result.comment == 0

        register_utilization_comment(
            comment_id,
            utilization_id,
            category,
            content,
            created,
            True,
            approved,
            user['id'],
        )

        refresh_utilization_comments(utilization_id)

        result = get_utilization(utilization_id)

        assert result.comment == 1

    @pytest.mark.db_test
    def test_get_resource_by_utilization_id(
        self, organization, dataset, resource, utilization
    ):
        result = get_resource_by_utilization_id(utilization.id)

        assert result
        assert result.organization_id == dataset['id']
        assert result.organization_name == organization['name']


class TestAttachedImageConfig:
    @patch('ckanext.feedback.services.utilization.details.get_upload_destination')
    @patch('ckanext.feedback.services.utilization.details.get_uploader')
    def test_get_attached_image_path(
        self, mock_get_uploader, mock_get_upload_destination
    ):
        attached_image_filename = 'attached_image_filename'

        mock_get_upload_destination.return_value = '/test/upload/path'

        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        get_attached_image_path(attached_image_filename)

        mock_get_upload_destination.assert_called_once()
        mock_get_uploader.assert_called_once()

    def test_get_upload_destination(self):
        assert get_upload_destination() == 'feedback_utilization_comment'


@pytest.mark.db_test
class TestAttachedImageService:
    def test_get_comment_attached_image_files(self, utilization_comment):
        result = get_comment_attached_image_files()

        assert result == ['test_attached_image.jpg']


@pytest.mark.db_test
class TestUtilizationCommentMoralCheckLog:
    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_create_utilization_comment_moral_check_log(self, utilization):
        utilization_id = utilization.id
        action = MoralCheckAction.INPUT_SELECTED
        input_comment = 'test_input_comment'
        suggested_comment = 'test_suggested_comment'
        output_comment = 'test_output_comment'

        create_utilization_comment_moral_check_log(
            utilization_id,
            action,
            input_comment,
            suggested_comment,
            output_comment,
        )
        session.flush()

        results = get_utilization_comment_moral_check_logs()

        assert results is not None
        assert results[0].utilization_id == utilization_id
        assert results[0].action == action
        assert results[0].input_comment == input_comment
        assert results[0].suggested_comment == suggested_comment
        assert results[0].output_comment == output_comment
        assert results[0].timestamp == datetime(2024, 1, 1, 15, 0, 0)

    def test_get_utilization_comment_moral_check_logs(
        self, utilization_comment_moral_check_log
    ):
        results = get_utilization_comment_moral_check_logs()

        assert results is not None
        assert results[0].id == utilization_comment_moral_check_log.id
        assert (
            results[0].utilization_id
            == utilization_comment_moral_check_log.utilization_id
        )
        assert results[0].action == utilization_comment_moral_check_log.action
        assert (
            results[0].input_comment
            == utilization_comment_moral_check_log.input_comment
        )
        assert (
            results[0].suggested_comment
            == utilization_comment_moral_check_log.suggested_comment
        )
        assert (
            results[0].output_comment
            == utilization_comment_moral_check_log.output_comment
        )
        assert results[0].timestamp == utilization_comment_moral_check_log.timestamp
