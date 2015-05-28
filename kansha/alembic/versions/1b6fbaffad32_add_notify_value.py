#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Add notify value

Revision ID: 1b6fbaffad32
Revises: d0e88000d3f
Create Date: 2013-11-04 09:59:21.968436

"""

# revision identifiers, used by Alembic.
revision = '1b6fbaffad32'
down_revision = 'd0e88000d3f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user_boards__board_members',
                  sa.Column('notify', sa.Integer, server_default='1'))


def downgrade():
    op.drop_column('user_boards__board_members', 'notify')
