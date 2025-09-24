import logging
import re

log = logging.getLogger(__name__)


class DataStoreDownloadMiddleware:
    def __init__(self, app):
        self.app = app
        self.datastore_dump_pattern = re.compile(r'/datastore/dump/([^?/]+)')

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        match = self.datastore_dump_pattern.match(path)

        def custom_start_response(status, headers, exc_info=None):
            if match:
                headers.append(('X-Feedback-Middleware', 'detected'))
                headers.append(('X-Feedback-Resource-ID', match.group(1)))
            return start_response(status, headers, exc_info)

        if match:
            resource_id = match.group(1)
            log.error("=== MIDDLEWARE DETECTED DATASTORE DOWNLOAD ===")
            log.error(f"=== Resource ID: {resource_id} ===")

            try:
                from ckanext.feedback.services.download.monthly import (
                    increment_resource_downloads_monthly,
                )
                from ckanext.feedback.services.download.summary import (
                    increment_resource_downloads,
                )

                increment_resource_downloads(resource_id)
                increment_resource_downloads_monthly(resource_id)
                log.error("=== MIDDLEWARE SUCCESSFULLY INCREMENTED COUNT ===")
            except Exception as e:
                log.error(f"=== MIDDLEWARE ERROR: {str(e)} ===")

        return self.app(environ, custom_start_response)
