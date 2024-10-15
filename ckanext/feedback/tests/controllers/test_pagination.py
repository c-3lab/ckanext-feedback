from unittest.mock import patch

import pytest

from ckanext.feedback.controllers.pagination import (
    _encode_params,
    _pager_url,
    get_pagination_value,
    search_url,
    url_with_params,
)


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestPagination:
    def test_encode_params(self):
        input_params = [('key1', 'value1'), ('key2', 'value2')]
        expected = [('key1', b'value1'), ('key2', b'value2')]
        assert _encode_params(input_params) == expected

    @patch('ckanext.feedback.controllers.pagination._encode_params')
    def test_url_with_params(self, mock_encode_params):
        mock_encode_params.return_value = [
            ('key1', b'value1'),
            ('key2', b'value2'),
            ('page', '1'),
        ]
        url = 'utilization/search'
        params = [('key1', 'value1'), ('key2', 'value2'), ('page', 1)]
        result = url_with_params(url, params)
        assert result == 'utilization/search?key1=value1&key2=value2&page=1'

    @patch('ckanext.feedback.controllers.pagination.url_with_params')
    @patch('ckanext.feedback.controllers.pagination.h.url_for')
    def test_search_url(self, mock_url_for, mock_url_with_params):
        url = 'utilization/search'
        mock_url_for.return_value = url
        mock_url_with_params.return_value = (
            'utilization/search?key1=value1&key2=value2&page=1'
        )

        params = [('key1', 'value1'), ('key2', 'value2'), ('page', 1)]
        result = search_url(params, url)
        assert result == 'utilization/search?key1=value1&key2=value2&page=1'

    @patch('ckanext.feedback.controllers.pagination.search_url')
    def test_pager_url(self, mock_search_url):
        mock_search_url.return_value = (
            'utilization/search?key1=value1&key2=value2&page=1'
        )
        params_nopage = [('key1', 'value1'), ('key2', 'value2')]
        endpoint = 'utilization/search'
        page = 1
        result = _pager_url(params_nopage, endpoint, page)
        assert result == 'utilization/search?key1=value1&key2=value2&page=1'

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
            'utilization/search?key1=value1&key2=value2&page=1'
        )
        endpoint = 'utilization.search'

        page, limit, offset, pager_url = get_pagination_value(endpoint)

        assert page == 1
        assert limit == 20
        assert offset == 0
        assert pager_url() == 'utilization/search?key1=value1&key2=value2&page=1'
