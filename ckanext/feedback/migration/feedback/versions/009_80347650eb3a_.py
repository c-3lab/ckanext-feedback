"""squash: replies approval cols, utilization_comment_reply, unique constraints


Revision ID: 80347650eb3a
Revises:8293443a0ff2
Create Date: 2025-09-16 02:03:04.363335

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '80347650eb3a'
down_revision = 'c64333d190eb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'resource_comment_reply',
        sa.Column(
            'approval', sa.BOOLEAN(), server_default=sa.text('FALSE'), nullable=False
        ),
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

    # Create a unique index to support ON CONFLICT (resource_id)
    op.create_unique_constraint(
        'uq_utilization_summary_resource_id',
        'utilization_summary',
        ['resource_id'],
    )

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

    # Add UNIQUE constraint to resource_id column
    op.create_unique_constraint(
        constraint_name='uq_download_summary_resource_id',
        table_name='download_summary',
        columns=['resource_id'],
    )
    op.add_column(
        'resource_comment_reply',
        sa.Column('attached_image_filename', sa.Text(), nullable=True),
    )
    op.add_column(
        'utilization_comment_reply',
        sa.Column('attached_image_filename', sa.Text(), nullable=True),
    )


def downgrade():
    # Remove UNIQUE constraint from resource_id column
    op.drop_column('resource_comment_reply', 'attached_image_filename')

    op.drop_constraint(
        constraint_name='uq_download_summary_resource_id',
        table_name='download_summary',
        type_='unique',
    )

    op.drop_index(
        'ix_ucreply_utilization_comment_id', table_name='utilization_comment_reply'
    )
    op.drop_table('utilization_comment_reply')

    op.drop_constraint(
        'uq_utilization_summary_resource_id',
        'utilization_summary',
        type_='unique',
    )

    op.drop_constraint(
        'resource_comment_reply_approval_user_id_fkey',
        'resource_comment_reply',
        type_='foreignkey',
    )
    op.drop_column('resource_comment_reply', 'approval_user_id')
    op.drop_column('resource_comment_reply', 'approved')
    op.drop_column('resource_comment_reply', 'approval')
