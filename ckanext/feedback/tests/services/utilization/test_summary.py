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
    UtilizationSummary,
)
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentReply,
    ResourceCommentSummary,
)
from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.models.issue import IssueResolution, IssueResolutionSummary
from ckanext.feedback.services.utilization.summary import (
    get_package_utilizations,
    get_resource_utilizations,
    create_utilization_summary,
    refresh_utilization_summary,
    get_package_issue_resolutions,
    get_resource_issue_resolutions,
    increment_issue_resolution_summary,
)


def get_utilization_summary(resource_id):
    return (
        session.query(UtilizationSummary)
        .filter(UtilizationSummary.resource_id == resource_id)
        .all()
    )


def get_issue_resolution_summary(utilization_id):
    return (
        session.query(IssueResolutionSummary)
        .filter(IssueResolutionSummary.utilization_id == utilization_id)
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

    def test_get_package_utilizations(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(id, resource['id'], title, description, False)

        get_package_utilizations(dataset['id']) == 1

    def test_get_resource_utilizations(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(id, resource['id'], title, description, False)

        get_resource_utilizations(resource['id']) == 1

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_create_utilization_summary(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(id, resource['id'], title, description, False)

        assert len(get_utilization_summary(resource['id'])) == 0

        create_utilization_summary(resource['id'])

        assert len(get_utilization_summary(resource['id'])) == 1

        create_utilization_summary(resource['id'])

        assert len(get_utilization_summary(resource['id'])) == 1

    def test_refresh_utilization_summary(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        id2 = str(uuid.uuid4())
        register_utilization(id, resource['id'], title, description, False)

        assert len(get_utilization_summary(resource['id'])) == 0

        refresh_utilization_summary(resource['id'])

        assert len(get_utilization_summary(resource['id'])) == 1
        assert get_utilization_summary(resource['id'])[0].utilization == 0

        register_utilization(id2, resource['id'], title, description, True)

        refresh_utilization_summary(resource['id'])

        assert len(get_utilization_summary(resource['id'])) == 1
        assert get_utilization_summary(resource['id'])[0].utilization == 1

    def test_get_package_issue_resolutions(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        time = datetime.now()

        register_utilization(id, resource['id'], title, description, True)

        assert get_package_issue_resolutions(dataset['id']) == 0

        session.add(
            IssueResolutionSummary(
                id=uuid.uuid4(),
                utilization_id=id,
                issue_resolution=1,
                created=time,
                updated=time,
            )
        )

        assert get_package_issue_resolutions(dataset['id']) == 1

    def test_get_resource_issue_resolutions(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        time = datetime.now()

        register_utilization(id, resource['id'], title, description, True)

        assert get_resource_issue_resolutions(resource['id']) == 0

        session.add(
            IssueResolutionSummary(
                id=uuid.uuid4(),
                utilization_id=id,
                issue_resolution=1,
                created=time,
                updated=time,
            )
        )

        assert get_resource_issue_resolutions(resource['id']) == 1

    def test_increment_issue_resolution_summary(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'

        register_utilization(id, resource['id'], title, description, True)

        increment_issue_resolution_summary(id)

        assert get_issue_resolution_summary(id).issue_resolution == 1

        increment_issue_resolution_summary(id)

        assert get_issue_resolution_summary(id).issue_resolution == 2
