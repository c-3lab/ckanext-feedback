import logging

from flask import Blueprint, request

from ckanext.feedback.services.download.monthly import (
    increment_resource_downloads_monthly,
)
from ckanext.feedback.services.download.summary import increment_resource_downloads

log = logging.getLogger(__name__)

# より強力にオーバーライドするためのBlueprint
datastore_blueprint = Blueprint(
    'feedback_datastore_override',
    __name__,
    url_prefix='',
)


# すべてのDataStore dumpリクエストをキャッチ
@datastore_blueprint.route('/datastore/dump/<resource_id>')
@datastore_blueprint.route('/datastore/dump/<resource_id>/')
@datastore_blueprint.before_app_request
def datastore_dump(resource_id=None):
    """DataStoreダウンロードをインターセプト"""

    # DataStoreダウンロードかどうかを判定
    if '/datastore/dump/' not in request.path:
        return  # DataStoreダウンロードではない場合は何もしない

    # URLからresource_idを抽出
    if not resource_id:
        import re

        match = re.search(r'/datastore/dump/([^/?]+)', request.path)
        resource_id = match.group(1) if match else None

    log.error("=== FEEDBACK PLUGIN INTERCEPTED DATASTORE DOWNLOAD ===")
    log.error(f"=== Request Path: {request.path} ===")
    log.error(f"=== Resource ID: {resource_id} ===")
    log.error(f"=== Query Params: {dict(request.args)} ===")

    # ダウンロードカウントを増加
    if resource_id:
        try:
            increment_resource_downloads(resource_id)
            increment_resource_downloads_monthly(resource_id)
            log.error("=== DOWNLOAD COUNT INCREMENTED SUCCESSFULLY ===")
        except Exception as e:
            log.error(f"=== ERROR INCREMENTING COUNT: {str(e)} ===")

    # 元のDataStore dump関数を呼び出し
    try:
        from ckanext.datastore.blueprint import dump as original_dump

        response = original_dump(resource_id)
        log.error("=== ORIGINAL DUMP FUNCTION CALLED SUCCESSFULLY ===")

        # デバッグヘッダー追加
        if hasattr(response, 'headers'):
            response.headers['X-Feedback-Intercepted'] = 'YES-WORKING'
            response.headers['X-Feedback-Resource-ID'] = resource_id

        return response
    except Exception as e:
        log.error(f"=== ERROR CALLING ORIGINAL DUMP: {str(e)} ===")
        raise


def get_datastore_download_blueprint():
    """Blueprint取得関数"""
    log.error("=== DATASTORE BLUEPRINT REQUESTED ===")
    return datastore_blueprint
