"""add_unique_index_on_utilization_summary_resource_id.py

Revision ID: 1d5459051d3a
Revises: 81aede0d41b3
Create Date: 2025-09-01 06:59:44.344888

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '1d5459051d3a'
down_revision = '81aede0d41b3'
branch_labels = None
depends_on = None


def upgrade():
    # Create a unique index to support ON CONFLICT (resource_id)
    op.create_unique_constraint(
        'uq_utilization_summary_resource_id',
        'utilization_summary',
        ['resource_id'],
    )


def downgrade():
    op.drop_constraint(
        'uq_utilization_summary_resource_id',
        'utilization_summary',
        type_='unique',
    )
