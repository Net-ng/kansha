#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""board background

Revision ID: 36d972f11e3e
Revises: 1b6fbaffad32
Create Date: 2014-02-11 12:01:02.395563

"""

# revision identifiers, used by Alembic.
revision = '36d972f11e3e'
down_revision = '1b6fbaffad32'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('board', sa.Column('background_image', sa.Unicode))
    op.add_column('board', sa.Column('background_position', sa.Unicode, server_default='repeat'))
    op.add_column('board', sa.Column('title_color', sa.Unicode))
    op.execute('''update board set background_position='repeat' where background_position is null''')


def downgrade():
    op.drop_column('board', 'background_image')
    op.drop_column('board', 'background_position')
    op.drop_column('board', 'title_color')
