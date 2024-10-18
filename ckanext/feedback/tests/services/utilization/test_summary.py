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
from ckanext.feedback.models.issue import IssueResolutionSummary
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization, UtilizationSummary
from ckanext.feedback.services.utilization.summary import (
    create_utilization_summary,
    get_package_issue_resolutions,
    get_package_utilizations,
    get_resource_issue_resolutions,
    get_resource_utilizations,
    increment_issue_resolution_summary,
    refresh_utilization_summary,
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


def register_utilization(id, resource_id, title, description, approval):
    utilization = Utilization(
        id=id,
        resource_id=resource_id,
        title=title,
        description=description,
        approval=approval,
    )
    session.add(utilization)


def resister_issue_resolution_summary(id, utilization_id, created, updated):
    issue_resolution_summary = IssueResolutionSummary(
        id=id,
        utilization_id=utilization_id,
        issue_resolution=1,
        created=created,
        updated=updated,
    )
    session.add(issue_resolution_summary)


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

        title = 'test title'
        description = 'test description'

        register_utilization(
            str(uuid.uuid4()), resource['id'], title, description, False
        )

        assert len(get_utilization_summary(resource['id'])) == 0

        refresh_utilization_summary(resource['id'])

        assert len(get_utilization_summary(resource['id'])) == 1
        assert get_utilization_summary(resource['id'])[0].utilization == 0

        register_utilization(
            str(uuid.uuid4()), resource['id'], title, description, True
        )

        refresh_utilization_summary(resource['id'])

        assert len(get_utilization_summary(resource['id'])) == 1
        assert get_utilization_summary(resource['id'])[0].utilization == 1

    def test_get_package_issue_resolutions(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        time = datetime.now()

        register_utilization(utilization_id, resource['id'], title, description, True)

        assert get_package_issue_resolutions(dataset['id']) == 0

        resister_issue_resolution_summary(str(uuid.uuid4()), utilization_id, time, time)

        assert get_package_issue_resolutions(dataset['id']) == 1

    def test_get_resource_issue_resolutions(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        time = datetime.now()

        register_utilization(utilization_id, resource['id'], title, description, True)

        assert get_resource_issue_resolutions(resource['id']) == 0

        resister_issue_resolution_summary(str(uuid.uuid4()), utilization_id, time, time)

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
