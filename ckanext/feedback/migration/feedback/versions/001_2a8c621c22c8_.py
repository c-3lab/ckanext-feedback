"""Add columns: rating_comment to resource_comment_summary, and url to utilization.

Revision ID: 2a8c621c22c8
Revises: 40bf9a900ef5
Create Date: 2024-05-22 02:36:08.154409

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2a8c621c22c8'
down_revision = '40bf9a900ef5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'resource_comment_summary', sa.Column('rating_comment', sa.Integer, default=0)
    )
    op.add_column('utilization', sa.Column('url', sa.Text))


def downgrade():
    op.drop_column('utilization', 'url')
    op.drop_column('resource_comment_summary', 'rating_comment')
