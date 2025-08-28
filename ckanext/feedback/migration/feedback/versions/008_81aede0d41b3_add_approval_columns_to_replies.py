"""add approval columns to replies

Revision ID: 81aede0d41b3
Revises: 8293443a0ff2
Create Date: 2025-08-28 08:06:02.475693

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '81aede0d41b3'
down_revision = '8293443a0ff2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'resource_comment_reply',
        sa.Column('approval', sa.BOOLEAN(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        'resource_comment_reply', sa.Column('approved', sa.TIMESTAMP(), nullable=True)
    )
    op.add_column(
        'resource_comment_reply',
        sa.Column('approval_user_id', sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        'resource_comment_reply_approval_user_id_fkey',
        'resource_comment_reply',
        'user',
        ['approval_user_id'],
        ['id'],
        onupdate='CASCADE',
        ondelete='SET NULL',
    )


def downgrade():
    def downgrade():
        op.drop_constraint(
            'resource_comment_reply_approval_user_id_fkey',
            'resource_comment_reply',
            type_='foreignkey',
        )
        op.drop_column('resource_comment_reply', 'approval_user_id')
        op.drop_column('resource_comment_reply', 'approved')
        op.drop_column('resource_comment_reply', 'approval')
