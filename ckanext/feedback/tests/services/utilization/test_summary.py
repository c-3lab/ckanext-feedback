import uuid
from datetime import datetime

import pytest

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


def get_registered_utilization_summary(resource_id):
    return (
        session.query(UtilizationSummary)
        .filter(UtilizationSummary.resource_id == resource_id)
        .first()
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
    session.commit()


def resister_issue_resolution_summary(id, utilization_id, created, updated):
    issue_resolution_summary = IssueResolutionSummary(
        id=id,
        utilization_id=utilization_id,
        issue_resolution=1,
        created=created,
        updated=updated,
    )
    session.add(issue_resolution_summary)
    session.commit()


@pytest.mark.db_test
class TestUtilizationDetailsService:
    def test_get_package_utilizations(self, dataset, resource):
        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(id, resource['id'], title, description, False)

        get_package_utilizations(dataset['id']) == 1

    def test_get_resource_utilizations(self, resource):
        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(id, resource['id'], title, description, False)

        get_resource_utilizations(resource['id']) == 1

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_create_utilization_summary(self, resource):
        create_utilization_summary(resource['id'])
        session.commit()
        utilization_summary = get_registered_utilization_summary(resource['id'])

        assert utilization_summary.resource_id == resource['id']
        assert utilization_summary.utilization == 0
        assert utilization_summary.created == datetime(2024, 1, 1, 15, 0, 0)
        assert utilization_summary.updated is None

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_refresh_utilization_summary(self, resource, utilization):
        refresh_utilization_summary(resource['id'])
        session.commit()
        utilization_summary = get_registered_utilization_summary(resource['id'])

        assert utilization_summary.resource_id == resource['id']
        assert utilization_summary.utilization == 1
        assert utilization_summary.created == datetime(2024, 1, 1, 15, 0, 0)
        assert utilization_summary.updated == datetime(2024, 1, 1, 15, 0, 0)

    def test_get_package_issue_resolutions(self, dataset, resource):
        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        time = datetime.now()

        register_utilization(utilization_id, resource['id'], title, description, True)

        assert get_package_issue_resolutions(dataset['id']) == 0

        resister_issue_resolution_summary(str(uuid.uuid4()), utilization_id, time, time)

        assert get_package_issue_resolutions(dataset['id']) == 1

    def test_get_resource_issue_resolutions(self, resource):
        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        time = datetime.now()

        register_utilization(utilization_id, resource['id'], title, description, True)

        assert get_resource_issue_resolutions(resource['id']) == 0

        resister_issue_resolution_summary(str(uuid.uuid4()), utilization_id, time, time)

        assert get_resource_issue_resolutions(resource['id']) == 1

    @pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
    def test_increment_issue_resolution_summary(self, utilization):
        increment_issue_resolution_summary(utilization.id)
        session.commit()
        issue_resolution_summary = get_issue_resolution_summary(utilization.id)

        assert issue_resolution_summary.utilization_id == utilization.id
        assert issue_resolution_summary.issue_resolution == 1
        assert issue_resolution_summary.created == datetime(2024, 1, 1, 15, 0, 0)
        assert issue_resolution_summary.updated == datetime(2024, 1, 1, 15, 0, 0)

        increment_issue_resolution_summary(utilization.id)
        session.commit()
        session.expire_all()
        issue_resolution_summary = get_issue_resolution_summary(utilization.id)

        assert issue_resolution_summary.utilization_id == utilization.id
        assert issue_resolution_summary.issue_resolution == 2
        assert issue_resolution_summary.created == datetime(2024, 1, 1, 15, 0, 0)
        assert issue_resolution_summary.updated == datetime(2024, 1, 1, 15, 0, 0)
