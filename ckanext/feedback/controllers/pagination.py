import logging
from functools import partial
from typing import Any, Iterable, Optional
from urllib.parse import urlencode

from ckan.common import config, request
from ckan.lib.helpers import helper_functions as h
from typing_extensions import TypeAlias

log = logging.getLogger(__name__)

Params: TypeAlias = "list[tuple[str, Any]]"


def _encode_params(params: Iterable[tuple[str, Any]]):
    return [(k, v.encode('utf-8') if isinstance(v, str) else str(v)) for k, v in params]


def url_with_params(url: str, params: Params) -> str:
    params = _encode_params(params)
    return url + '?' + urlencode(params)


def search_url(params: Params, endpoint) -> str:
    url = h.url_for(endpoint)
    return url_with_params(url, params)


def _pager_url(params_nopage: Params, endpoint, page: Optional[int] = None) -> str:
    params = list(params_nopage)
    params.append(('page', page))
    return search_url(params, endpoint)


def get_pagination_value(endpoint):
    page = h.get_page_number(request.args)

    limit = config.get('ckan.datasets_per_page')
    offset = (page - 1) * limit

    params_nopage = []
    for k, v in request.args.items(multi=True):
        if k != 'page':
            params_nopage += [(k, v)]

    pager_url = partial(_pager_url, params_nopage, endpoint=endpoint)

    return page, limit, offset, pager_url
