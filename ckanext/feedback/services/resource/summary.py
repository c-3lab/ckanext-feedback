import logging
from datetime import datetime

from ckan.model.resource import Resource
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentSummary,
)
from ckanext.feedback.models.session import session

log = logging.getLogger(__name__)


# Get comments of the target package
def get_package_comments(package_id):
    count = (
        session.query(func.sum(ResourceCommentSummary.comment))
        .join(Resource)
        .filter(
            Resource.package_id == package_id,
            Resource.state == "active",
        )
        .scalar()
    )
    return count or 0


# Get comments of the target resource
def get_resource_comments(resource_id):
    count = (
        session.query(ResourceCommentSummary.comment)
        .filter(ResourceCommentSummary.resource_id == resource_id)
        .scalar()
    )
    return count or 0


# Get rating of the target package
def get_package_rating(package_id):
    row = (
        session.query(
            func.sum(
                ResourceCommentSummary.rating * ResourceCommentSummary.rating_comment
            ).label('total_rating'),
            func.sum(ResourceCommentSummary.rating_comment).label('rating_comment'),
        )
        .join(Resource)
        .filter(
            Resource.package_id == package_id,
            Resource.state == "active",
        )
        .first()
    )
    if row and row.rating_comment and row.rating_comment > 0:
        return row.total_rating / row.rating_comment
    else:
        return 0


# Get rating of the target resource
def get_resource_rating(resource_id):
    log.warning("─" * 80)
    log.warning(f"[QUERY] get_resource_rating called for resource_id: {resource_id}")
    log.warning("[QUERY] Session state BEFORE query execution:")
    log.warning(f"  - session object: {session}")
    log.warning(f"  - session type: {type(session)}")

    # 重要な内部状態を確認
    trans_value = getattr(session, '_transaction', 'N/A')
    log.warning(f"  - _transaction: {trans_value}")

    if session._transaction is not None:
        is_active_value = getattr(session._transaction, 'is_active', 'N/A')
        log.warning(f"  - _transaction.is_active: {is_active_value}")
        log.warning("  - ✅ _transaction exists (READY TO QUERY)")
    else:
        log.warning("  - ❌ _transaction is None (WILL FAIL!)")

    is_active = getattr(session, 'is_active', 'N/A')
    log.warning(f"  - session.is_active: {is_active}")
    bind_value = getattr(session, 'bind', 'N/A')
    log.warning(f"  - bind: {bind_value}")

    try:
        log.warning(
            "[QUERY] Executing: session.query(ResourceCommentSummary.rating)..."
        )
        rating = (
            session.query(ResourceCommentSummary.rating)
            .filter(ResourceCommentSummary.resource_id == resource_id)
            .scalar()
        )

        # クエリ成功後の状態
        log.warning("[QUERY] ✅ Query executed successfully!")
        log.warning(f"  - Result: {rating}")
        log.warning("[QUERY] Session state AFTER successful query:")
        trans_after = getattr(session, '_transaction', 'N/A')
        log.warning(f"  - _transaction: {trans_after}")
        is_active_after = getattr(session, 'is_active', 'N/A')
        log.warning(f"  - is_active: {is_active_after}")
        log.warning("─" * 80)

        return rating or 0

    except Exception as e:
        # クエリ失敗時の詳細情報
        log.error("[QUERY] ❌ Query FAILED!")
        log.error(f"  - Error type: {type(e).__name__}")
        log.error(f"  - Error message: {e}")
        log.error("[QUERY] Session state when error occurred:")
        trans_error = getattr(session, '_transaction', 'N/A')
        log.error(f"  - _transaction: {trans_error}")
        is_active_error = getattr(session, 'is_active', 'N/A')
        log.error(f"  - is_active: {is_active_error}")
        log.error("[QUERY] Full traceback:")

        import traceback

        log.error(traceback.format_exc())
        log.warning("─" * 80)
        raise


# Create new resource summary
def create_resource_summary(resource_id):
    summary = insert(ResourceCommentSummary).values(
        resource_id=resource_id,
    )
    summary = summary.on_conflict_do_nothing(index_elements=['resource_id'])
    session.execute(summary)


# Recalculate approved ratings and comments related to the resource summary
def refresh_resource_summary(resource_id):
    now = datetime.now()

    total_rating = (
        session.query(
            func.sum(ResourceComment.rating),
        )
        .filter(
            ResourceComment.resource_id == resource_id,
            ResourceComment.approval,
            ResourceComment.rating.isnot(None),
        )
        .scalar()
    )
    if total_rating is None:
        total_rating = 0
    total_comment = (
        session.query(ResourceComment)
        .filter(
            ResourceComment.resource_id == resource_id,
            ResourceComment.approval,
            ResourceComment.rating.isnot(None),
        )
        .count()
    )
    if total_comment > 0:
        rating = total_rating / total_comment
        rating_comment = total_comment
    else:
        rating = 0
        rating_comment = 0

    comment = (
        session.query(ResourceComment)
        .filter(
            ResourceComment.resource_id == resource_id,
            ResourceComment.approval,
            ResourceComment.content.isnot(None),
        )
        .count()
    )

    insert_summary = insert(ResourceCommentSummary).values(
        resource_id=resource_id,
        rating=rating,
        comment=comment,
        rating_comment=rating_comment,
    )
    summary = insert_summary.on_conflict_do_update(
        index_elements=['resource_id'],
        set_={
            'rating': insert_summary.excluded.rating,
            'comment': insert_summary.excluded.comment,
            'rating_comment': insert_summary.excluded.rating_comment,
            'updated': now,
        },
    )
    session.execute(summary)
