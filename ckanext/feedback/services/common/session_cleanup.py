"""
セッションクリーンアップのためのヘルパー関数とデコレーター

PR #302で追加されたsession.close()の目的:
- Identity Mapをクリアして重複レコード問題を防ぐ

この実装:
- session.expunge_all()を使用してIdentity Mapのみをクリア
- session._transactionは破壊しない（AttributeError回避）
- teardown_app_requestを使わず、必要な関数でのみクリーンアップ
"""

import logging
from functools import wraps

from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


def cleanup_feedback_session():
    """
    feedbackのsessionをクリーンアップ

    Identity Mapをクリアして、次のリクエストで古いキャッシュを参照しないようにする
    """
    try:
        session.expunge_all()
        log.debug("Feedback session cleaned up (Identity Map cleared)")
    except Exception as e:
        log.error(f"Failed to cleanup feedback session: {e}")


def with_session_cleanup(func):
    """
    デコレーター: 関数実行後にsessionをクリーンアップ

    使用例:
        @with_session_cleanup
        def my_controller_function():
            # ... 処理 ...
            session.commit()
            # ← 自動的にexpunge_all()が呼ばれる
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # 関数が正常終了しても、例外が発生しても必ずクリーンアップ
            cleanup_feedback_session()

    return wrapper
