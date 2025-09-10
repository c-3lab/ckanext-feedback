"""empty message

Revision ID: 64f3177a129c
Revises: 16f60ff92113
Create Date: 2025-09-02 05:05:53.405425

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '64f3177a129c'
down_revision = '16f60ff92113'
branch_labels = None
depends_on = None


def upgrade():
    # Add UNIQUE constraint to resource_id column
    op.create_unique_constraint(
        constraint_name='unique_resource_id',
        table_name='download_summary',
        columns=['resource_id'],
    )


def downgrade():
    # Remove UNIQUE constraint from resource_id column
    op.drop_constraint(
        constraint_name='unique_resource_id',
        table_name='download_summary',
        type_='unique',
    )
