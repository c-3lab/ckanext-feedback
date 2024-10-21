"""empty message

Revision ID: b883d604a877
Revises: 2a8c621c22c8
Create Date: 2024-10-21 02:00:17.129102

"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b883d604a877'
down_revision = '2a8c621c22c8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'resource_like',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'resource_id',
            sa.Text,
            sa.ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('like_count', sa.Integer, default=0),
        sa.Column('created', sa.TIMESTAMP, default=datetime.now),
        sa.Column('updated', sa.TIMESTAMP),
    )


def downgrade():
    op.drop_table('resource_like')
