# ckanext/feedback/views/datastore_download.py
import logging

from flask import Blueprint

from ckanext.feedback.services.download.monthly import (
    increment_resource_downloads_monthly,
)
from ckanext.feedback.services.download.summary import increment_resource_downloads

log = logging.getLogger(__name__)

datastore_blueprint = Blueprint(
    'datastore_download',
    __name__,
)


@datastore_blueprint.route('/datastore/dump/<resource_id>')
def datastore_dump(resource_id):
    # ダウンロードカウントをインクリメント
    log.info(
        f"Incrementing download count for resource {resource_id} via datastore route"
    )
    increment_resource_downloads(resource_id)
    increment_resource_downloads_monthly(resource_id)

    # 元のDataStoreのdump関数を呼び出す
    from ckanext.datastore.blueprint import dump as original_dump

    return original_dump(resource_id)


def get_datastore_download_blueprint():
    return datastore_blueprint
