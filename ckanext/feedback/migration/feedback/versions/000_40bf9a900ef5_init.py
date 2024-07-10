"""Create tables for feedback plugin

Revision ID: 40bf9a900ef5
Revises:
Create Date: 2024-05-30 04:24:42.871134

"""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from ckan.common import _

# revision identifiers, used by Alembic.
revision = '40bf9a900ef5'
down_revision = None
branch_labels = None
depends_on = None


class ResourceCommentCategory(enum.Enum):
    REQUEST = _('Request')
    QUESTION = _('Question')
    THANK = _('Thank')


class UtilizationCommentCategory(enum.Enum):
    REQUEST = _('Request')
    QUESTION = _('Question')
    THANK = _('Thank')


def upgrade():
    """
    今後の実装でckan feedback initコマンドに相当するcreate tableを書く予定
    """
    op.create_table(
        'utilization',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'resource_id',
            sa.Text,
            sa.ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('title', sa.Text),
        sa.Column('description', sa.Text),
        sa.Column('comment', sa.Integer, default=0),
        sa.Column('created', sa.TIMESTAMP, default=datetime.now),
        sa.Column('approval', sa.BOOLEAN, default=False),
        sa.Column('approved', sa.TIMESTAMP),
        sa.Column(
            'approval_user_id',
            sa.Text,
            sa.ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL'),
        ),
    )
    op.create_table(
        'utilization_comment',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'utilization_id',
            sa.Text,
            sa.ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('category', sa.Enum(UtilizationCommentCategory), nullable=False),
        sa.Column('content', sa.Text),
        sa.Column('created', sa.TIMESTAMP, default=datetime.now),
        sa.Column('approval', sa.BOOLEAN, default=False),
        sa.Column('approved', sa.TIMESTAMP),
        sa.Column(
            'approval_user_id',
            sa.Text,
            sa.ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL'),
        ),
    )
    op.create_table(
        'utilization_summary',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'resource_id',
            sa.Text,
            sa.ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('utilization', sa.Integer, default=0),
        sa.Column('created', sa.TIMESTAMP, default=datetime.now),
        sa.Column('updated', sa.TIMESTAMP),
    )
    op.create_table(
        'issue_resolution',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'utilization_id',
            sa.Text,
            sa.ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('description', sa.Text),
        sa.Column('created', sa.TIMESTAMP, default=datetime.now),
        sa.Column(
            'creator_user_id',
            sa.Text,
            sa.ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL'),
        ),
    )
    op.create_table(
        'issue_resolution_summary',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'utilization_id',
            sa.Text,
            sa.ForeignKey('utilization.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('issue_resolution', sa.Integer),
        sa.Column('created', sa.TIMESTAMP, default=datetime.now),
        sa.Column('updated', sa.TIMESTAMP),
    )
    op.create_table(
        'resource_comment',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'resource_id',
            sa.Text,
            sa.ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('category', sa.Enum(ResourceCommentCategory)),
        sa.Column('content', sa.Text),
        sa.Column('rating', sa.Integer),
        sa.Column('created', sa.TIMESTAMP, default=datetime.now),
        sa.Column('approval', sa.BOOLEAN, default=False),
        sa.Column('approved', sa.TIMESTAMP),
        sa.Column(
            'approval_user_id',
            sa.Text,
            sa.ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL'),
        ),
    )
    op.create_table(
        'resource_comment_reply',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'resource_comment_id',
            sa.Text,
            sa.ForeignKey(
                'resource_comment.id', onupdate='CASCADE', ondelete='CASCADE'
            ),
            nullable=False,
        ),
        sa.Column('content', sa.Text),
        sa.Column('created', sa.TIMESTAMP, default=datetime.now),
        sa.Column(
            'creator_user_id',
            sa.Text,
            sa.ForeignKey('user.id', onupdate='CASCADE', ondelete='SET NULL'),
        ),
    )
    op.create_table(
        'resource_comment_summary',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'resource_id',
            sa.Text,
            sa.ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('comment', sa.Integer, default=0),
        sa.Column('rating', sa.Float, default=0),
        sa.Column('created', sa.TIMESTAMP, default=datetime.now),
        sa.Column('updated', sa.TIMESTAMP),
    )
    op.create_table(
        'download_summary',
        sa.Column('id', sa.Text, default=uuid.uuid4, primary_key=True, nullable=False),
        sa.Column(
            'resource_id',
            sa.Text,
            sa.ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('download', sa.Integer),
        sa.Column('created', sa.TIMESTAMP),
        sa.Column('updated', sa.TIMESTAMP),
    )


def downgrade():
    op.drop_table('download_summary')
    op.drop_table('resource_comment_summary')
    op.drop_table('resource_comment_reply')
    op.drop_table('resource_comment')
    op.drop_table('issue_resolution_summary')
    op.drop_table('issue_resolution')
    op.drop_table('utilization_summary')
    op.drop_table('utilization_comment')
    op.drop_table('utilization')
    op.execute('DROP TYPE IF EXISTS utilizationcommentcategory;')
    op.execute('DROP TYPE IF EXISTS resourcecommentcategory;')
