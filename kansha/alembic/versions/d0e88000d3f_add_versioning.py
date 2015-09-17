#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Add versioning

Revision ID: d0e88000d3f
Revises: b740362087
Create Date: 2013-10-30 10:45:11.526568

"""

# revision identifiers, used by Alembic.
revision = 'd0e88000d3f'
down_revision = 'b740362087'

from alembic import context, op
from nagare import database
import sqlalchemy as sa

from kansha.board import models


def upgrade():
    op.add_column('board', sa.Column('version', sa.Integer, server_default='0'))


def downgrade():
    op.drop_column('board', 'version')
