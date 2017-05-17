"""Rename board.archive

Revision ID: 361f9cbae3fc
Revises: 2b0edcfa57b4
Create Date: 2015-12-18 17:00:10.034124

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '361f9cbae3fc'
down_revision = '2b0edcfa57b4'


def upgrade():
    with op.batch_alter_table('board') as batch_op:
        batch_op.alter_column('archive', new_column_name='show_archive')


def downgrade():
    with op.batch_alter_table('board') as batch_op:
        batch_op.alter_column('show_archive', new_column_name='archive')
