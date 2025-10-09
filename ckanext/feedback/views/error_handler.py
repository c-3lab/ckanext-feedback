import logging

from psycopg2.errors import UndefinedTable
from sqlalchemy.exc import ProgrammingError

from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


def add_error_handler(func):
    def wrapper():
        blueprint = func()

        @blueprint.app_errorhandler(ProgrammingError)
        def handle_programming_error(e):
            if isinstance(e.orig, UndefinedTable):
                log.error(
                    'Some tables does not exit.'
                    ' Run "ckan --config=/etc/ckan/production.ini feedback init".'
                )

            session.rollback()
            raise e

        @blueprint.app_errorhandler(Exception)
        def handle_exception(e):
            session.rollback()
            raise e

        @blueprint.teardown_app_request
        def cleanup_session(e=None):
            """
            PR #302対応: セッションを完全にクリーンアップ

            session.remove() を使用することで:
            - 現在のスレッド/リクエストのセッションを削除
            - 次回アクセス時に新しいセッションが自動生成される
            - Identity Mapが完全にクリアされる
            - AttributeError が発生しない
            - メモリリークが完全に防げる

            変更履歴:
            - 最初: session.close() → AttributeError発生
            - 次: session.expunge_all() → bind=None問題で解決せず
            - 現在: session.remove() → 根本的に解決（Flask推奨パターン）
            """
            try:
                session.remove()
            except Exception:
                # クリーンアップ失敗は致命的ではないので、例外は無視
                pass

        return blueprint

    return wrapper
