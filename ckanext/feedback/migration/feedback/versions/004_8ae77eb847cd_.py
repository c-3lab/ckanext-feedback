"""Create tables: resource_like_monthly

Revision ID: 8ae77eb847cd
Revises: 4c5922f300d6
Create Date: 2025-03-24 01:31:32.035788

"""

import uuid

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '8ae77eb847cd'
down_revision = '4c5922f300d6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'resource_like_monthly',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'resource_id',
            sa.Text,
            sa.ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('like_count', sa.Integer),
        sa.Column('created', sa.TIMESTAMP),
        sa.Column('updated', sa.TIMESTAMP),
    )


def downgrade():
    op.drop_table('resource_like_monthly')
