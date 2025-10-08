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
            log.warning("[ERROR_HANDLER] よばれ")
            """
            リクエスト終了時のセッションクリーンアップ

            close()の代わりにexpunge_all()を使用する理由：
            - グローバルセッションオブジェクトを壊さない
            - Identity Mapのキャッシュはクリアされる
            - 接続はSQLAlchemyが自動管理
            - 次のリクエストでも安全に使用可能
            """
            log.warning("=" * 80)
            log.warning(
                "[CLEANUP] teardown_app_request called - Starting session cleanup"
            )

            # === クリーンアップ前の状態を記録 ===
            log.warning("[CLEANUP] Session state BEFORE cleanup:")
            log.warning(f"  - session object: {session}")
            log.warning(f"  - _transaction: {getattr(session, '_transaction', 'N/A')}")
            log.warning(f"  - is_active: {getattr(session, 'is_active', 'N/A')}")
            log.warning(f"  - bind: {getattr(session, 'bind', 'N/A')}")
            identity_map_size = len(getattr(session, 'identity_map', {}))
            log.warning(f"  - identity_map size: {identity_map_size}")
            new_count = len(getattr(session, 'new', []))
            log.warning(f"  - new objects: {new_count}")
            dirty_count = len(getattr(session, 'dirty', []))
            log.warning(f"  - dirty objects: {dirty_count}")
            deleted_count = len(getattr(session, 'deleted', []))
            log.warning(f"  - deleted objects: {deleted_count}")

            try:
                # === ステップ1: rollback() ===
                log.warning("[CLEANUP] Step 1: Executing rollback()...")
                if session.is_active:
                    log.warning("  → Transaction is active, rolling back")
                    log.warning("[ERROR_HANDLER] ろーるばっく")
                    session.rollback()
                    log.warning("  → rollback() completed successfully")
                else:
                    log.warning("  → Transaction is not active, skipping rollback")

                # rollback()後の状態を確認
                log.warning("[CLEANUP] Session state AFTER rollback():")
                trans_after_rollback = getattr(session, '_transaction', 'N/A')
                log.warning(f"  - _transaction: {trans_after_rollback}")
                is_active_after_rollback = getattr(session, 'is_active', 'N/A')
                log.warning(f"  - is_active: {is_active_after_rollback}")

                # === ステップ2: expunge_all() ===
                log.warning("[CLEANUP] Step 2: Executing expunge_all()...")
                log.warning("  → Clearing Identity Map (removing all cached objects)")
                session.expunge_all()
                log.warning("  → expunge_all() completed successfully")

                # expunge_all()後の状態を確認
                log.warning("[CLEANUP] Session state AFTER expunge_all():")
                identity_map_size_after = len(getattr(session, 'identity_map', {}))
                log.warning(f"  - identity_map size: {identity_map_size_after}")

                # === 最終状態 ===
                log.warning("[CLEANUP] Final session state:")
                log.warning(
                    f"  - _transaction: {getattr(session, '_transaction', 'N/A')}"
                )
                log.warning(f"  - is_active: {getattr(session, 'is_active', 'N/A')}")
                log.warning(f"  - bind: {getattr(session, 'bind', 'N/A')}")
                log.warning(f"  - identity_map size: {identity_map_size_after}")

                log.warning("[CLEANUP] ✅ Session cleanup completed successfully!")
                log.warning("=" * 80)

            except Exception as cleanup_error:
                log.error(
                    f"[CLEANUP] ❌ Session cleanup failed: {cleanup_error}",
                    exc_info=True,
                )
                log.error("[CLEANUP] Attempting emergency rollback...")
                try:
                    session.rollback()
                    log.error("[CLEANUP] Emergency rollback successful")
                except Exception as emergency_error:
                    log.error(
                        f"[CLEANUP] Emergency rollback failed: {emergency_error}",
                        exc_info=True,
                    )
                log.warning("=" * 80)

        return blueprint

    return wrapper
