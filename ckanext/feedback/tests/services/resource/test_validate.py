import pytest
from ckan import model

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.services.resource import validate


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestComments:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = model.meta.engine
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def test_validate_with_valid_comment(self):
        example_valid_comment = 'example comment'
        result = validate.validate_comment(example_valid_comment)
        assert result is None

    def test_validate_with_invalid_comment(self):
        example_invalid_comment = 'ex'
        for _ in range(9):
            example_invalid_comment += example_invalid_comment
        result = validate.validate_comment(example_invalid_comment)
        assert result == 'Please keep the comment length below 1000'
