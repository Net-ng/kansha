"""add display week numbers

Revision ID: 1bd634091036
Revises: 4fb34b202c5f
Create Date: 2015-09-15 11:51:46.739150

"""

# revision identifiers, used by Alembic.
revision = '1bd634091036'
down_revision = '4fb34b202c5f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('display_week_numbers', sa.Boolean))


def downgrade():
    op.drop_column('user', 'display_week_numbers')
