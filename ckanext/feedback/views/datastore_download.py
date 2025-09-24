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

    try:
        increment_resource_downloads(resource_id)
        increment_resource_downloads_monthly(resource_id)
        count_success = True
    except Exception as e:
        log.error(f"Error incrementing download count: {str(e)}")
        count_success = False

    # 元のDataStoreのdump関数を呼び出す
    from ckanext.datastore.blueprint import dump as original_dump

    response = original_dump(resource_id)

    # デバッグ用ヘッダーを追加
    if hasattr(response, 'headers'):
        response.headers['X-Feedback-Intercepted'] = 'true'
        response.headers['X-Feedback-Count-Success'] = str(count_success)

    return response


def get_datastore_download_blueprint():
    return datastore_blueprint
