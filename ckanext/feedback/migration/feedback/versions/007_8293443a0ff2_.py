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

import click
from alembic import op

# revision identifiers, used by Alembic.
revision = '8293443a0ff2'
down_revision = '070e83e52e6b'
branch_labels = None
depends_on = None


def delete_duplicates(conn, table, unique_column, order_columns):
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
    result = conn.execute(sql)
    deleted_rows = result.fetchall()
    click.secho(
        f"Removed {len(deleted_rows)} duplicate record(s) from the '{table}' table.",
        fg='green',
    )


def upgrade():
    conn = op.get_bind()
    delete_duplicates(
        conn,
        'resource_comment_summary',
        'resource_id',
        ['updated DESC', 'comment DESC'],
    )
    delete_duplicates(
        conn, 'utilization_summary', 'resource_id', ['updated DESC', 'utilization DESC']
    )
    delete_duplicates(
        conn, 'resource_like', 'resource_id', ['updated DESC', 'like_count DESC']
    )
    delete_duplicates(
        conn, 'download_summary', 'resource_id', ['updated DESC', 'download DESC']
    )
    delete_duplicates(
        conn,
        'issue_resolution_summary',
        'utilization_id',
        ['updated DESC', 'issue_resolution DESC'],
    )
    delete_duplicates(
        conn, 'resource_comment_reactions', 'resource_comment_id', ['updated DESC']
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
