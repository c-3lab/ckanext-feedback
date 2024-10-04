import logging

import ckan.views.resource as resource
from flask import request

from ckanext.feedback.services.common import config as feedback_config
from ckanext.feedback.services.download.summary import increment_resource_downloads
from ckanext.feedback.services.resource.comment import get_resource

log = logging.getLogger(__name__)


class DownloadController:
    # extend default download function to count when a resource is downloaded
    @staticmethod
    def extended_download(package_type, id, resource_id, filename=None):
        if filename is None:
            filename = get_resource(resource_id).Resource.url

        if (
            request.headers.get('Sec-Fetch-Dest') == 'document'
            or request.args.get('user-download') == 'true'
        ):
            increment_resource_downloads(resource_id)

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

        c_d_value = response.headers.get('Content-Disposition')
        if c_d_value:
            c_d_value = c_d_value.replace('inline', 'attachment')
        else:
            c_d_value = 'attachment'
        if 'filename' not in c_d_value:
            c_d_value = f'{c_d_value}; filename="{filename}"'
        response.headers.set('Content-Disposition', c_d_value)

        return response
