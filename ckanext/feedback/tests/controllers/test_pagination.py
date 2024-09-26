from unittest.mock import patch

import pytest

from ckanext.feedback.controllers.pagination import get_pagination_value


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestPagination:
    @patch('ckanext.feedback.controllers.pagination._pager_url')
    @patch('ckanext.feedback.controllers.pagination.h.url_for')
    @patch('ckanext.feedback.controllers.pagination.h.get_page_number')
    @patch('ckanext.feedback.controllers.pagination.request.args')
    @patch('ckanext.feedback.controllers.pagination.config')
    def test_get_pagination_value(
        self,
        mock_config,
        mock_request_args,
        mock_get_page_number,
        mock_url_for,
        mock_pager_url,
    ):
        mock_get_page_number.return_value = 1
        mock_request_args.return_value = {'page': 1}
        mock_request_args.items.return_value = [
            ('key1', 'value1'),
            ('key2', 'value2'),
            ('page', 1),
        ]
        mock_config.get.return_value = 20
        mock_url_for.return_value = 'utilization/search'
        mock_pager_url.return_value = (
            'utilization/search?key1=value1&key2=value2&page=2'
        )
        endpoint = 'utilization.search'

        page, limit, offset, pager_url = get_pagination_value(endpoint)

        assert page == 1
        assert limit == 20
        assert offset == 0
        assert pager_url() == 'utilization/search?key1=value1&key2=value2&page=2'
