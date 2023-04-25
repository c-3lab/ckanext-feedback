import uuid
from datetime import datetime

import ckan.tests.factories as factories
import pytest
from ckan import model

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization
from ckanext.feedback.services.utilization.search import get_utilizations


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


engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestUtilizationDetailsService:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_get_utilizations(self):
        unapproved_dataset = factories.Dataset()
        unapproved_resource = factories.Resource(package_id=unapproved_dataset['id'])
        unapproved_id = str(uuid.uuid4())
        unapproved_title = 'unapproved title'

        approved_dataset = factories.Dataset()
        approved_resource = factories.Resource(package_id=approved_dataset['id'])
        approved_id = str(uuid.uuid4())
        approved_title = 'approved title'

        description = 'test description'
        register_utilization(
            unapproved_id,
            unapproved_resource['id'],
            unapproved_title,
            description,
            False,
            datetime(1999, 1, 2, 3, 4),
        )
        register_utilization(
            approved_id,
            approved_resource['id'],
            approved_title,
            description,
            True,
            datetime(2000, 1, 2, 3, 4),
        )

        unapproved_utilization = (
            unapproved_id,
            unapproved_title,
            0,
            datetime(1999, 1, 2, 3, 4),
            False,
            unapproved_resource['name'],
            unapproved_resource['id'],
            unapproved_dataset['name'],
            0,
        )

        approved_utilization = (
            approved_id,
            approved_title,
            0,
            datetime(2000, 1, 2, 3, 4),
            True,
            approved_resource['name'],
            approved_resource['id'],
            approved_dataset['name'],
            0,
        )

        # with no argument
        assert get_utilizations() == [approved_utilization, unapproved_utilization]

        # with package_id
        assert get_utilizations(id=unapproved_dataset['id']) == [unapproved_utilization]

        # with resource_id
        assert get_utilizations(id=approved_resource['id']) == [approved_utilization]

        # with keyword
        assert get_utilizations(keyword='unapproved') == [unapproved_utilization]

        # with approval
        assert get_utilizations(approval=True) == [approved_utilization]
