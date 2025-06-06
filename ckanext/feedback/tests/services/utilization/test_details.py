import uuid
from datetime import datetime

import ckan.tests.factories as factories
import pytest
from ckan import model

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.issue import IssueResolution
from ckanext.feedback.models.session import session
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
    get_issue_resolutions,
    get_utilization,
    get_utilization_comment_categories,
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
        create_resource_like_tables(engine)
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
