#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""adding max cards

Revision ID: b740362087
Revises: 537fa16b46e7
Create Date: 2013-09-19 17:37:37.027495

"""

# revision identifiers, used by Alembic.
revision = 'b740362087'
down_revision = '537fa16b46e7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('column', sa.Column('nb_max_cards', sa.Integer))


def downgrade():
    op.drop_column('column', 'nb_max_cards')
