"""Create tables: resource_comment_reactions, utilization_comment_reactions
and enums: resourcecommentresponsestatus, utilizationcommentresponsestatus
Revision ID: 87954668dbb2
Revises: 070e83e52e6b
Create Date: 2025-05-20 04:37:59.281689
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op

from ckanext.feedback.models.types import ResourceCommentResponseStatusType

# revision identifiers, used by Alembic.
revision = '87954668dbb2'
down_revision = '8ae77eb847cd'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'resource_comment_reactions',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'resource_comment_id',
            sa.Text,
            sa.ForeignKey(
                'resource_comment.id', onupdate='CASCADE', ondelete='CASCADE'
            ),
            nullable=False,
        ),
        sa.Column('response_status', ResourceCommentResponseStatusType, nullable=False),
        sa.Column('admin_liked', sa.BOOLEAN, default=False),
        sa.Column('created', sa.TIMESTAMP, default=datetime.now),
        sa.Column('updated', sa.TIMESTAMP),
        sa.Column(
            'updater_user_id',
            sa.Text,
            sa.ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL'),
        ),
    )


def downgrade():
    op.drop_table('resource_comment_reactions')
    op.execute('DROP TYPE IF EXISTS resourcecommentresponsestatus;')
