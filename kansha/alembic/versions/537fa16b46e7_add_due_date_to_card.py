#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Add due_date to cards

Revision ID: 537fa16b46e7
Revises: None
Create Date: 2013-09-10 16:44:45.986636

"""

# revision identifiers, used by Alembic.
revision = '537fa16b46e7'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('card', sa.Column('due_date', sa.Date))


def downgrade():
    op.drop_column('card', 'due_date')
