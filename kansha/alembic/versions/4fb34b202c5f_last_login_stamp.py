#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""last_login stamp

Revision ID: 4fb34b202c5f
Revises: 6cb3c668d65
Create Date: 2015-05-18 19:00:56.564336

"""

import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4fb34b202c5f'
down_revision = '6cb3c668d65'


def upgrade():
    last_login = sa.Column('last_login', sa.DateTime)
    op.add_column('user', last_login)

    # last_login mustn't be empty for already existing users
    user = sa.table(
        'user',
        last_login,
        sa.Column('email_to_confirm', sa.Unicode(255))
    )
    op.execute(
        user.update().where(
            user.c.email_to_confirm == None  # noqa
        ).values({'last_login': datetime.datetime.now()})
    )


def downgrade():
    op.drop_column('user', 'last_login')
