"""new asset path to assets

Revision ID: 24be36b8c67
Revises: 1bd634091036
Create Date: 2015-10-23 15:43:39.398148

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '24be36b8c67'
down_revision = '1bd634091036'

users = sa.Table(
    'user',
    sa.MetaData(),
    sa.Column('username', sa.VARCHAR(255), primary_key=True),
    sa.Column('picture', sa.Text)
)


def fix_path(oldpath):
    if not oldpath:
        return oldpath
    return oldpath.replace('/assets/', '/services/assets_manager/')


def restore_path(newpath):
    if not newpath:
        return newpath
    return newpath.replace('/services/assets_manager/', '/assets/')


def upgrade():
    connection = op.get_bind()
    for u in connection.execute(users.select()):
        connection.execute(
            users.update().where(
                users.c.username == u.username
            ).values(
                picture=fix_path(u.picture)
            )
        )


def downgrade():
    connection = op.get_bind()
    for u in connection.execute(users.select()):
        connection.execute(
            users.update().where(
                users.c.username == u.username
            ).values(
                picture=restore_path(u.picture)
            )
        )
