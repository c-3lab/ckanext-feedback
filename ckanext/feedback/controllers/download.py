from ckanext.feedback.services.download.summary import increment_resource_downloads
from ckan.views.resource import download
from flask import request


class DownloadController:
    def increment_resource_downloads(resource_id):
        increment_resource_downloads(resource_id)

    # extend default download function to count when a resource is downloaded
    def extended_download(package_type, id, resource_id, filename=None):
        if request.headers.get('Sec-Fetch-Dest') == 'document':
            increment_resource_downloads(resource_id)
        return download(package_type, id, resource_id, filename=filename)
