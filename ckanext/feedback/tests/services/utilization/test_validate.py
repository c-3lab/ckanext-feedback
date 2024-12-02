import pytest
from ckan import model

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.services.utilization import validate

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

    def test_validate_with_valid_url(self):
        example_valid_url = 'https://example.com'
        result = validate.validate_url(example_valid_url)
        assert result is None

    def test_validate_with_invalid_url(self):
        example_invalid_url = 'invalid_url'
        result = validate.validate_url(example_invalid_url)
        assert result == 'Please provide a valid URL'

    def test_validate_with_invalid_url_len(self):
        example_domain = 'ex'
        for _ in range(10):
            example_domain += example_domain
        result = validate.validate_url('https://' + example_domain + '.com')
        assert result == 'Please keep the URL length below 2048'

    def test_validate_with_valid_title(self):
        example_valid_title = 'example title'
        result = validate.validate_title(example_valid_title)
        assert result is None

    def test_validate_with_invalid_title(self):
        example_invalid_title = (
            'example title'
            'example title'
            'example title'
            'example title'
            'example title'
        )
        result = validate.validate_title(example_invalid_title)
        assert result == 'Please keep the title length below 50'

    def test_validate_with_valid_description(self):
        example_valid_description = 'example description'
        result = validate.validate_description(example_valid_description)
        assert result is None

    def test_validate_with_invalid_description(self):
        example_invalid_description = 'ex'
        for _ in range(11):
            example_invalid_description += example_invalid_description
        result = validate.validate_description(example_invalid_description)
        assert result == 'Please keep the description length below 2000'

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
