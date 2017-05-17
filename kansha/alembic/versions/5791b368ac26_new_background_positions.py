"""new_background_positions

Revision ID: 5791b368ac26
Revises: 443501b69d16
Create Date: 2017-04-27 11:03:20.788762

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '5791b368ac26'
down_revision = '443501b69d16'


def upgrade():
    op.alter_column('board', 'background_position', nullable=True, server_default=None)
    board = sa.Table(
        'board',
        sa.MetaData(),
        sa.Column('background_position', sa.Unicode),
    )
    bind = op.get_bind()
    bind.execute(
        board.update().where(
            board.c.background_position == u'repeat'
        ).values(background_position=u'tile')
    )
    bind.execute(
        board.update().where(
            board.c.background_position == u'cover'
        ).values(background_position=u'fill')
    )


def downgrade():
    pass
