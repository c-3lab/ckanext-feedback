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

from alembic import op

# revision identifiers, used by Alembic.
revision = '8293443a0ff2'
down_revision = '070e83e52e6b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DELETE FROM resource_comment_summary
        WHERE id NOT IN (
            SELECT id FROM (
                SELECT DISTINCT ON (resource_id) id
                FROM resource_comment_summary
                ORDER BY resource_id, updated DESC, comment DESC
            ) AS keep_rows
        );
    """
    )
    op.execute(
        """
        DELETE FROM utilization_summary
        WHERE id NOT IN (
            SELECT id FROM (
                SELECT DISTINCT ON (resource_id) id
                FROM utilization_summary
                ORDER BY resource_id, updated DESC, utilization DESC
            ) AS keep_rows
        );
    """
    )
    op.execute(
        """
        DELETE FROM resource_like
        WHERE id NOT IN (
            SELECT id FROM (
                SELECT DISTINCT ON (resource_id) id
                FROM resource_like
                ORDER BY resource_id, updated DESC, like_count DESC
            ) AS keep_rows
        );
    """
    )
    op.execute(
        """
        DELETE FROM download_summary
        WHERE id NOT IN (
            SELECT id FROM (
                SELECT DISTINCT ON (resource_id) id
                FROM download_summary
                ORDER BY resource_id, updated DESC, download DESC
            ) AS keep_rows
        );
    """
    )
    op.execute(
        """
        DELETE FROM issue_resolution_summary
        WHERE id NOT IN (
            SELECT id FROM (
                SELECT DISTINCT ON (utilization_id) id
                FROM issue_resolution_summary
                ORDER BY utilization_id, updated DESC, issue_resolution DESC
            ) AS keep_rows
        );
    """
    )
    op.execute(
        """
        DELETE FROM resource_comment_reactions
        WHERE id NOT IN (
            SELECT id FROM (
                SELECT DISTINCT ON (resource_comment_id) id
                FROM resource_comment_reactions
                ORDER BY resource_comment_id, updated DESC
            ) AS keep_rows
        );
    """
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
