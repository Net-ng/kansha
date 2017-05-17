"""empty message

Revision ID: 2c0a3788227
Revises: f058ce7ee0c
Create Date: 2016-01-20 17:18:51.047928

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '2c0a3788227'
down_revision = 'f058ce7ee0c'


def upgrade():
    bind = op.get_bind()
    if bind.engine.name != 'sqlite':
        op.drop_column('user', 'display_week_numbers')


def downgrade():
    op.add_column('user', sa.Column('display_week_numbers', sa.Boolean))
