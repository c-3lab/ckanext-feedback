import pytest
import ckan.tests.factories as factories
import uuid
from ckan.model import Resource

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
from ckanext.feedback.services.utilization.registration import (
    get_resource,
    create_utilization
)


def get_utilization(resource_id):
    return (
        session.query(
            Utilization.title,
            Utilization.description,
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

    def test_get_resource(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        result = get_resource(resource['id'])

        assert result.id == resource['id']
        assert result.package_id == resource['package_id']
        assert result.name == resource['name']
        assert result.description == resource['description']
        assert result.format == resource['format']
        assert result.url == resource['url']

    def test_create_utilization(self):
        resource = factories.Resource()

        title = 'test title'
        description = 'test description'

        assert get_utilization(resource['id']) is None

        create_utilization(
            resource['id'],
            title,
            description
        )

        result = get_utilization(resource['id'])

        assert result.title == title
        assert result.description == description
