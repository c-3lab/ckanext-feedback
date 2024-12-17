import logging
import os
from urllib.parse import urlparse

import ckan.views.resource as resource
import requests
from ckan.plugins import toolkit
from flask import Response, request

from ckanext.feedback.services.common import config as feedback_config
from ckanext.feedback.services.download.monthly import (
    increment_resource_downloads_monthly,
)
from ckanext.feedback.services.download.summary import increment_resource_downloads
from ckanext.feedback.services.resource.comment import get_resource

log = logging.getLogger(__name__)


class DownloadController:
    # extend default download function to count when a resource is downloaded
    @staticmethod
    def extended_download(package_type, id, resource_id, filename=None):
        if filename is None:
            filename = get_resource(resource_id).Resource.url

        user_download = toolkit.asbool(request.args.get('user-download'))
        if request.headers.get('Sec-Fetch-Dest') == 'document' or user_download:
            increment_resource_downloads(resource_id)
            increment_resource_downloads_monthly(resource_id)

        handler = feedback_config.download_handler()
        if not handler:
            log.debug('Use default CKAN callback for resource.download')
            handler = resource.download
        response = handler(
            package_type=package_type,
            id=id,
            resource_id=resource_id,
            filename=filename,
        )

        if user_download:
            if response.status_code == 302:
                url = response.headers.get('Location')
                log.debug(f"Download to redirect URL.[{url}]")
                filename = os.path.basename(urlparse(url).path)
                try:
                    redirect_response = requests.get(url, allow_redirects=True)
                    external_response = Response(
                        redirect_response.content,
                        headers=dict(redirect_response.headers),
                        content_type=redirect_response.headers['Content-Type'],
                    )
                except requests.exceptions.ConnectionError:
                    log.exception(f'Cannot connect to external resource. URL[{url}]')
                    return response
                if external_response.status_code != 200:
                    log.exception(f'Failure to acquire external resource. URL[{url}]')
                    return response
                response = external_response

            c_d_value = response.headers.get('Content-Disposition')
            if c_d_value:
                c_d_value = c_d_value.replace('inline', 'attachment')
            else:
                c_d_value = 'attachment'
            if 'filename' not in c_d_value:
                c_d_value = f'{c_d_value}; filename="{filename}"'
            response.headers['Content-Disposition'] = c_d_value

        return response
