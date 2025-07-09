"""Add columns for attached image for resource comment and utilization comment

Revision ID: 070e83e52e6b
Revises: 8ae77eb847cd
Create Date: 2025-04-09 05:57:55.887801

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '070e83e52e6b'
down_revision = '87954668dbb2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('utilization_comment', sa.Column('attached_image_filename', sa.Text))
    op.add_column('resource_comment', sa.Column('attached_image_filename', sa.Text))


def downgrade():
    op.drop_column('utilization_comment', 'attached_image_filename')
    op.drop_column('resource_comment', 'attached_image_filename')
