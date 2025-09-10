"""empty message

Revision ID: 16f60ff92113
Revises: 1d5459051d3a
Create Date: 2025-09-01 08:45:14.763945

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '16f60ff92113'
down_revision = '1d5459051d3a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'utilization_comment_reply',
        sa.Column('id', sa.Text(), primary_key=True, nullable=False),
        sa.Column('utilization_comment_id', sa.Text(), nullable=False),
        sa.Column('content', sa.Text()),
        sa.Column('created', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
        sa.Column('approval', sa.BOOLEAN(), server_default=sa.text('FALSE')),
        sa.Column('approved', sa.TIMESTAMP()),
        sa.Column('approval_user_id', sa.Text()),
        sa.Column('creator_user_id', sa.Text()),
        sa.ForeignKeyConstraint(
            ['utilization_comment_id'],
            ['utilization_comment.id'],
            name='fk_ucreply_comment',
            onupdate='CASCADE',
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['approval_user_id'],
            ['user.id'],
            name='fk_ucreply_approval_user',
            onupdate='CASCADE',
            ondelete='SET NULL',
        ),
        sa.ForeignKeyConstraint(
            ['creator_user_id'],
            ['user.id'],
            name='fk_ucreply_creator_user',
            onupdate='CASCADE',
            ondelete='SET NULL',
        ),
    )
    op.create_index(
        'ix_ucreply_utilization_comment_id',
        'utilization_comment_reply',
        ['utilization_comment_id'],
    )


def downgrade():
    op.drop_index(
        'ix_ucreply_utilization_comment_id', table_name='utilization_comment_reply'
    )
    op.drop_table('utilization_comment_reply')
