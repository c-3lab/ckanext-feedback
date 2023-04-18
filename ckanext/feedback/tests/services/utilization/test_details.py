import pytest
import ckan.tests.factories as factories
import uuid

from datetime import datetime
from ckan import model
from ckanext.feedback.command.feedback import (
    get_engine,
    create_utilization_tables,
    create_resource_tables,
    create_download_tables,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
)
from ckanext.feedback.models.issue import IssueResolution
from ckanext.feedback.services.utilization.details import (
    get_utilization,
    approve_utilization,
    get_utilization_comments,
    create_utilization_comment,
    approve_utilization_comment,
    get_utilization_comment_categories,
    create_issue_resolution,
    get_issue_resolutions,
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


def register_utilization(id, resource_id, title, description, approval):
    utilization = Utilization(
        id=id,
        resource_id=resource_id,
        title=title,
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
#        engine = get_engine('db', '5432', 'ckan_test', 'ckan', 'ckan')
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_get_utilization(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        assert get_registered_utilization(resource['id']) is None

        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(id, resource['id'], title, description, False)

        registered_utilization = get_registered_utilization(resource['id'])
        result = get_utilization(registered_utilization.id)
        fake_utilization = (
            title,
            description,
            0,
            False,
            resource['name'],
            resource['id'],
            dataset['name'],
        )
        assert result == fake_utilization

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_approve_utilization(self):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])
        test_datetime = datetime.now()

        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(id, resource['id'], title, description, False)

        utilization_before_approved = get_registered_utilization(resource['id'])
        approve_utilization(utilization_before_approved.id, user['id'])
        utilization_after_approved = get_registered_utilization(resource['id'])
        fake_utilization = (id, True, test_datetime, user['id'])
        assert utilization_after_approved == fake_utilization

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilization_comments_approval_is_none(self):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(utilization_id, resource['id'], title, description, False)
        registered_utilization = get_registered_utilization(resource['id'])

        created = datetime.now()
        approved = datetime.now()
        comment_id_one = str(uuid.uuid4())
        category_request = UtilizationCommentCategory.REQUEST
        content_one = 'test content1'
        register_utilization_comment(
            comment_id_one,
            registered_utilization.id,
            category_request,
            content_one,
            created,
            False,
            None,
            None,
        )
        utilization_comments = get_utilization_comments(registered_utilization.id, None)

        assert len(utilization_comments) == 1
        registered_utilization_comment = convert_utilization_comment_to_tuple(
            utilization_comments[0]
        )
        fake_utilization_comment_not_approved = (
            comment_id_one,
            registered_utilization.id,
            category_request,
            content_one,
            created,
            False,
            None,
            None,
        )
        assert registered_utilization_comment == fake_utilization_comment_not_approved

        comment_id_two = str(uuid.uuid4())
        category_thank = UtilizationCommentCategory.THANK
        content_two = 'test content2'
        register_utilization_comment(
            comment_id_two,
            registered_utilization.id,
            category_thank,
            content_two,
            datetime(2001, 1, 2, 3, 4),
            True,
            approved,
            user['id'],
        )
        utilization_comments = get_utilization_comments(None, None)

        assert len(utilization_comments) == 2
        utilization_comment_approved = convert_utilization_comment_to_tuple(
            utilization_comments[0]
        )
        utilization_comment_not_approved = convert_utilization_comment_to_tuple(
            utilization_comments[1]
        )
        fake_utilization_comment_approved = (
            comment_id_two,
            registered_utilization.id,
            category_thank,
            content_two,
            datetime(2001, 1, 2, 3, 4),
            True,
            approved,
            user['id'],
        )
        assert utilization_comment_not_approved == fake_utilization_comment_not_approved
        assert utilization_comment_approved == fake_utilization_comment_approved

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilization_comments_approval_is_false(self):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(utilization_id, resource['id'], title, description, False)
        registered_utilization = get_registered_utilization(resource['id'])

        created = datetime.now()
        approved = datetime.now()
        comment_id_not_approved = str(uuid.uuid4())
        comment_id_approved = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'

        register_utilization_comment(
            comment_id_not_approved,
            registered_utilization.id,
            category,
            content,
            created,
            False,
            None,
            None,
        )
        register_utilization_comment(
            comment_id_approved,
            registered_utilization.id,
            category,
            content,
            created,
            True,
            approved,
            user['id'],
        )
        utilization_comments = get_utilization_comments(
            registered_utilization.id, False
        )

        assert len(utilization_comments) == 1
        utilization_comment_not_approved = convert_utilization_comment_to_tuple(
            utilization_comments[0]
        )
        fake_utilization_comment_not_approved = (
            comment_id_not_approved,
            registered_utilization.id,
            category,
            content,
            created,
            False,
            None,
            None,
        )
        assert utilization_comment_not_approved == fake_utilization_comment_not_approved

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilization_comments_approval_is_true(self):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(utilization_id, resource['id'], title, description, False)
        registered_utilization = get_registered_utilization(resource['id'])

        created = datetime.now()
        approved = datetime.now()
        comment_id_not_approved = str(uuid.uuid4())
        comment_id_approved = str(uuid.uuid4())
        category = UtilizationCommentCategory.ADVERTISE
        content = 'test content'

        register_utilization_comment(
            comment_id_not_approved,
            registered_utilization.id,
            category,
            content,
            created,
            False,
            None,
            None,
        )
        register_utilization_comment(
            comment_id_approved,
            registered_utilization.id,
            category,
            content,
            created,
            True,
            approved,
            user['id'],
        )
        utilization_comments = get_utilization_comments(registered_utilization.id, True)

        assert len(utilization_comments) == 1
        utilization_comment_approved = convert_utilization_comment_to_tuple(
            utilization_comments[0]
        )
        fake_utilization_comment_approved = (
            comment_id_approved,
            registered_utilization.id,
            category,
            content,
            created,
            True,
            approved,
            user['id'],
        )
        assert utilization_comment_approved == fake_utilization_comment_approved

    def test_create_utilization_comment(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(utilization_id, resource['id'], title, description, False)
        registered_utilization = get_registered_utilization(resource['id'])

        category = UtilizationCommentCategory.REQUEST
        content = 'test content'
        create_utilization_comment(registered_utilization.id, category, content)

        registered_utilization_comment = get_registered_utilization_comment(
            registered_utilization.id
        )
        utilization_comment = registered_utilization_comment[0]
        assert utilization_comment.utilization_id == registered_utilization.id
        assert utilization_comment.category == category
        assert utilization_comment.content == content
        assert utilization_comment.approval is False
        assert utilization_comment.approved is None
        assert utilization_comment.approval_user_id is None

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_approve_utilization_comment(self):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(utilization_id, resource['id'], title, description, False)
        registered_utilization = get_registered_utilization(resource['id'])

        created = datetime.now()
        comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'
        register_utilization_comment(
            comment_id,
            registered_utilization.id,
            category,
            content,
            created,
            False,
            None,
            None,
        )

        registered_utilization_comment = get_registered_utilization_comment(
            registered_utilization.id
        )
        comment_id = registered_utilization_comment[0].id
        approve_utilization_comment(comment_id, user['id'])
        updated_utilization_comment = get_registered_utilization_comment(
            registered_utilization.id
        )[0]

        assert updated_utilization_comment.category == category
        assert updated_utilization_comment.content == content
        assert updated_utilization_comment.approval is True
        assert updated_utilization_comment.approved == datetime.now()
        assert updated_utilization_comment.approval_user_id == user['id']

    def test_get_utilization_comment_categories(self):
        assert get_utilization_comment_categories() == UtilizationCommentCategory

    def test_get_issue_resolutions(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        user = factories.User()

        session.add(
            Utilization(
                resource_id=resource['id'],
                title='test_utilization',
                description='test_utilization_description',
            )
        )

        registered_utilization = get_registered_utilization(resource['id'])
        assert get_registered_issue_resolution(registered_utilization.id) is None
        description = 'test_issue_resolution_description'
        time = datetime.now()

        session.add(
            IssueResolution(
                utilization_id=registered_utilization.id,
                description=description,
                created=time,
                creator_user_id=user['id'],
            )
        )

        issue_resolution = get_issue_resolutions(registered_utilization.id)[0]

        assert issue_resolution.utilization_id == registered_utilization.id
        assert issue_resolution.description == description
        assert issue_resolution.created == time
        assert issue_resolution.creator_user_id == user['id']

    def test_create_issue_resolution(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        user = factories.Sysadmin()

        session.add(
            Utilization(
                resource_id=resource['id'],
                title='test_utilization',
                description='test_utilization_description',
            )
        )

        registered_utilization = get_registered_utilization(resource['id'])
        description = 'test_issue_resolution_description'
        create_issue_resolution(registered_utilization.id, description, user['id'])

        issue_resolution = (registered_utilization.id, description, user['id'])

        assert (
            get_registered_issue_resolution(registered_utilization.id)
            == issue_resolution
        )

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_refresh_utilization_comments(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        user = factories.Sysadmin()

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        created = datetime.now()
        approved = datetime.now()
        comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.QUESTION
        content = 'test content'

        register_utilization(utilization_id, resource['id'], title, description, True)

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

        result_utilization = get_utilization(utilization_id)

        assert result_utilization.comment == 1
