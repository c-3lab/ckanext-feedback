"""Add columns for attached image for resource comment and utilization comment

Revision ID: 6f044c5ed092
Revises: 4c5922f300d6
Create Date: 2025-02-28 05:12:22.318915

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '6f044c5ed092'
down_revision = '4c5922f300d6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('utilization_comment', sa.Column('attached_image_filename', sa.Text))
    op.add_column('resource_comment', sa.Column('attached_image_filename', sa.Text))


def downgrade():
    op.drop_column('utilization_comment', 'attached_image_filename')
    op.drop_column('resource_comment', 'attached_image_filename')
