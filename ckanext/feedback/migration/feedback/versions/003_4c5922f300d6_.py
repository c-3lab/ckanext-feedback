"""empty message
Revision ID: 4c5922f300d6
Revises: b883d604a877
Create Date: 2024-10-28 00:41:13.653438
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4c5922f300d6'
down_revision = 'b883d604a877'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'download_monthly',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'resource_id',
            sa.Text,
            sa.ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('download_count', sa.Integer),
        sa.Column('created', sa.TIMESTAMP, default=datetime.now),
        sa.Column('updated', sa.TIMESTAMP),
    )


def downgrade():
    op.drop_table('download_monthly')
