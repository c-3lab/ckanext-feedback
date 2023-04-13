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
from ckanext.feedback.services.utilization.search import (
    get_utilizations
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


def register_utilization(id, resource_id, title, description, approval, created):
    utilization = Utilization(
        id=id,
        resource_id=resource_id,
        title=title,
        description=description,
        approval=approval,
        created=created,
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


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestUtilizationDetailsService:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = get_engine('db', '5432', 'ckan_test', 'ckan', 'ckan')
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilizations(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        dataset2 = factories.Dataset()
        resource2 = factories.Resource(package_id=dataset2['id'])

        id = str(uuid.uuid4())
        id2 = str(uuid.uuid4())
        title = 'unapproved title'
        title2 = 'approved title'
        description = 'test description'
        register_utilization(id, resource['id'], title, description, False, datetime.now())
        register_utilization(id2, resource2['id'], title2, description, True, datetime.now())

        unapproved_utilization = (
            id,
            title,
            0,
            datetime(2000, 1, 2, 3, 4),
            False,
            resource['name'],
            resource['id'],
            dataset['name'],
            0,
        )

        approved_utilization = (
            id2,
            title2,
            0,
            datetime(2000, 1, 2, 3, 4),
            True,
            resource2['name'],
            resource2['id'],
            dataset2['name'],
            0,
        )

        # with no argument
        assert get_utilizations() == [approved_utilization, unapproved_utilization]

        # with package_id
        assert get_utilizations(id=dataset['id']) == [unapproved_utilization]

        # with resource_id
        assert get_utilizations(id=resource2['id']) == [approved_utilization]

        # with keyword
        assert get_utilizations(keyword='unapproved') == [unapproved_utilization]

        # with approval
        assert get_utilizations(approval=True) == [approved_utilization]
