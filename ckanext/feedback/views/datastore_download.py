import logging

from flask import Blueprint

from ckanext.feedback.services.download.monthly import (
    increment_resource_downloads_monthly,
)
from ckanext.feedback.services.download.summary import increment_resource_downloads

log = logging.getLogger(__name__)

# DataStoreダウンロード用Blueprint
datastore_blueprint = Blueprint(
    'feedback_datastore_override',
    __name__,
    url_prefix='',
)


@datastore_blueprint.route('/datastore/dump/<resource_id>')
@datastore_blueprint.route('/datastore/dump/<resource_id>/')
def datastore_dump(resource_id):
    """DataStoreダウンロードをインターセプトしてカウントを増加"""
    log.error("=== FEEDBACK PLUGIN INTERCEPTED DATASTORE DOWNLOAD ===")
    log.error(f"=== Resource ID: {resource_id} ===")

    # ダウンロードカウントを増加
    try:
        increment_resource_downloads(resource_id)
        increment_resource_downloads_monthly(resource_id)
        count_success = True
        log.error("=== DOWNLOAD COUNT INCREMENTED SUCCESSFULLY ===")
    except Exception as e:
        log.error(f"=== ERROR INCREMENTING COUNT: {str(e)} ===")
        count_success = False

    # 元のDataStore dump関数を呼び出し
    try:
        from ckanext.datastore.blueprint import dump as original_dump

        response = original_dump(resource_id)
        log.error("=== ORIGINAL DUMP FUNCTION CALLED SUCCESSFULLY ===")
    except Exception as e:
        log.error(f"=== ERROR CALLING ORIGINAL DUMP: {str(e)} ===")
        raise

    # デバッグ用ヘッダーを追加
    if hasattr(response, 'headers'):
        response.headers['X-Feedback-Intercepted'] = 'YES-WORKING'
        response.headers['X-Feedback-Count-Success'] = str(count_success)
        response.headers['X-Feedback-Resource-ID'] = resource_id

    return response


def get_datastore_download_blueprint():
    """Blueprint取得関数"""
    log.error("=== DATASTORE BLUEPRINT REQUESTED ===")
    return datastore_blueprint
