import pytest
from ckan import model

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.services.utilization.validate import validate_url

engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestUtilizationDetailsService:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_validate_with_valid_url(self):
        example_valid_url = 'https://example.com'
        result = validate_url(example_valid_url)
        assert result == []

    def test_validate_with_invalid_url(self):
        example_invalid_url = 'invalid_url'
        result = validate_url(example_invalid_url)
        assert result == ['Please provide a valid URL']
