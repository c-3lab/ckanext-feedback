"""Remove duplicate data and add unique constraints

Tables affected:
- resource_comment_summary
- utilization_summary
- resource_like
- download_summary
- issue_resolution_summary
- resource_comment_reactions

Revision ID: 8293443a0ff2
Revises: 070e83e52e6b
Create Date: 2025-08-01 04:31:53.115172

"""

from datetime import datetime

import click
from alembic import op
from sqlalchemy.exc import SQLAlchemyError

# revision identifiers, used by Alembic.
revision = '8293443a0ff2'
down_revision = '070e83e52e6b'
branch_labels = None
depends_on = None


def log_message(level, message, color=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

    if not color:
        click.secho(
            f"{timestamp} {level} {message}",
        )
    else:
        click.secho(
            f"{timestamp} {level} {message}",
            fg=color,
        )


def delete_duplicates(table, unique_column, order_columns):
    conn = op.get_bind()

    sql = f"""
        DELETE FROM {table}
        WHERE id NOT IN (
            SELECT id FROM (
                SELECT DISTINCT ON ({unique_column}) id
                FROM {table}
                ORDER BY {unique_column}, {', '.join(order_columns)}
            ) AS keep_rows
        )
        RETURNING id;
    """

    try:
        result = conn.execute(sql)
        deleted_rows = result.fetchall()

        log_message(
            "INFO",
            f"Removed {len(deleted_rows)} duplicate record(s) "
            f"from the '{table}' table.",
        )

    except SQLAlchemyError:
        log_message(
            "ERROR",
            "END - Duplicate record removal: Failed",
            "red",
        )
        log_message(
            "INFO",
            "-" * 80,
        )
        raise


def upgrade():
    log_message(
        "INFO",
        "-" * 80,
    )
    log_message(
        "INFO",
        "START - Duplicate record removal for unique constraint",
    )

    delete_duplicates(
        'resource_comment_summary',
        'resource_id',
        ['updated DESC', 'comment DESC'],
    )
    delete_duplicates(
        'utilization_summary', 'resource_id', ['updated DESC', 'utilization DESC']
    )
    delete_duplicates(
        'resource_like', 'resource_id', ['updated DESC', 'like_count DESC']
    )
    delete_duplicates(
        'download_summary', 'resource_id', ['updated DESC', 'download DESC']
    )
    delete_duplicates(
        'issue_resolution_summary',
        'utilization_id',
        ['updated DESC', 'issue_resolution DESC'],
    )
    delete_duplicates(
        'resource_comment_reactions', 'resource_comment_id', ['updated DESC']
    )

    log_message(
        "SUCCESS",
        "END - Duplicate record removal: Completed",
        "green",
    )
    log_message(
        "INFO",
        "-" * 80,
    )

    op.create_unique_constraint(
        'resource_comment_summary_resource_id_ukey',
        'resource_comment_summary',
        ['resource_id'],
    )
    op.create_unique_constraint(
        'utilization_summary_resource_id_ukey', 'utilization_summary', ['resource_id']
    )
    op.create_unique_constraint(
        'resource_like_resource_id_ukey', 'resource_like', ['resource_id']
    )
    op.create_unique_constraint(
        'download_summary_resource_id_ukey', 'download_summary', ['resource_id']
    )
    op.create_unique_constraint(
        'issue_resolution_summary_utilization_id_ukey',
        'issue_resolution_summary',
        ['utilization_id'],
    )
    op.create_unique_constraint(
        'resource_comment_reactions_resource_comment_id_ukey',
        'resource_comment_reactions',
        ['resource_comment_id'],
    )


def downgrade():
    op.drop_constraint(
        'resource_comment_summary_resource_id_ukey',
        'resource_comment_summary',
        type_='unique',
    )
    op.drop_constraint(
        'utilization_summary_resource_id_ukey', 'utilization_summary', type_='unique'
    )
    op.drop_constraint(
        'resource_like_resource_id_ukey', 'resource_like', type_='unique'
    )
    op.drop_constraint(
        'download_summary_resource_id_ukey', 'download_summary', type_='unique'
    )
    op.drop_constraint(
        'issue_resolution_summary_utilization_id_ukey',
        'issue_resolution_summary',
        type_='unique',
    )
    op.drop_constraint(
        'resource_comment_reactions_resource_comment_id_ukey',
        'resource_comment_reactions',
        type_='unique',
    )
