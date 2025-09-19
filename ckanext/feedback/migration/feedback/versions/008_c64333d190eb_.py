"""Add moral check log tables for resource and utilization comments

Tables added:
- resource_comment_moral_check_log
- utilization_comment_moral_check_log

These tables store logs of moral check actions
for comments on resources and utilizations.
"""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c64333d190eb'
down_revision = '8293443a0ff2'
branch_labels = None
depends_on = None


class MoralCheckAction(enum.Enum):
    CHECK_COMPLETED = 'CheckCompleted'
    PREVIOUS_CONFIRM = 'PreviousConfirm'
    PREVIOUS_SUGGESTION = 'PreviousSuggestion'
    INPUT_SELECTED = 'InputSelected'
    SUGGESTION_SELECTED = 'SuggestionSelected'


def upgrade():
    op.create_table(
        'resource_comment_moral_check_log',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'resource_id',
            sa.Text,
            sa.ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'action',
            sa.Enum(MoralCheckAction, name='resourcecomment_moralcheckaction'),
            nullable=False,
        ),
        sa.Column('input_comment', sa.Text),
        sa.Column('suggested_comment', sa.Text),
        sa.Column('output_comment', sa.Text),
        sa.Column('timestamp', sa.TIMESTAMP, default=datetime.now),
    )
    op.create_table(
        'utilization_comment_moral_check_log',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'utilization_id',
            sa.Text,
            sa.ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'action',
            sa.Enum(MoralCheckAction, name='utilizationcomment_moralcheckaction'),
            nullable=False,
        ),
        sa.Column('input_comment', sa.Text),
        sa.Column('suggested_comment', sa.Text),
        sa.Column('output_comment', sa.Text),
        sa.Column('timestamp', sa.TIMESTAMP, default=datetime.now),
    )


def downgrade():
    op.drop_table('resource_comment_moral_check_log')
    op.drop_table('utilization_comment_moral_check_log')
    op.execute('DROP TYPE IF EXISTS resourcecomment_moralcheckaction;')
    op.execute('DROP TYPE IF EXISTS utilizationcomment_moralcheckaction;')
