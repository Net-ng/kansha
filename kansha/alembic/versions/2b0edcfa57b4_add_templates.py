"""Add templates

Revision ID: 2b0edcfa57b4
Revises: 24be36b8c67
Create Date: 2015-11-24 17:50:13.280722

"""

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = '2b0edcfa57b4'
down_revision = '24be36b8c67'

DEFAULT_LABELS = (
    (u'Green', u'#22C328'),
    (u'Red', u'#CC3333'),
    (u'Blue', u'#3366CC'),
    (u'Yellow', u'#D7D742'),
    (u'Orange', u'#DD9A3C'),
    (u'Purple', u'#8C28BD')
)


boards = sa.Table(
    'board',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('title', sa.Unicode(255)),
    sa.Column('is_template', sa.Boolean, default=False),
    sa.Column('comments_allowed', sa.Integer, default=1),
    sa.Column('votes_allowed', sa.Integer, default=1),
    sa.Column('description', sa.UnicodeText, default=u''),
    sa.Column('visibility', sa.Integer, default=0),
    sa.Column('version', sa.Integer, default=0, server_default='0'),
    sa.Column('uri', sa.Unicode(255), index=True, unique=True),
    sa.Column('archive', sa.Integer, default=0),
    sa.Column('archived', sa.Boolean, default=False),
    sa.Column('weighting_cards', sa.Integer, default=0),
    sa.Column('weights', sa.Unicode(255), default=u'')
)

columns = sa.Table(
    'column',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('title', sa.Unicode(200)),
    sa.Column('index', sa.Integer),
    sa.Column('nb_max_cards', sa.Integer),
    sa.Column('archive', sa.Boolean, default=False),
    sa.Column('board_id', sa.Integer)
)

labels = sa.Table(
    'label',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('title', sa.Unicode(255)),
    sa.Column('color', sa.Unicode(255)),
    sa.Column('board_id', sa.Integer),
    sa.Column('index', sa.Integer)
)


def upgrade():
    bind = op.get_bind()

    # Add column
    op.add_column('board', sa.Column('is_template', sa.Boolean, default=lambda: False))

    bind.execute(boards.update().values(is_template=False))

    # Empty board
    insert = boards.insert({'title': u'Empty board',
                            'is_template': True,
                            'visibility': 1})
    board_id = bind.execute(insert).inserted_primary_key[0]
    for index, (title, color) in enumerate(DEFAULT_LABELS):
        insert = labels.insert({'title': title,
                                'color': color,
                                'index': index,
                                'board_id': board_id})
        bind.execute(insert)

    # Todo board
    insert = boards.insert({'title': u'Todo',
                            'is_template': True,
                            'visibility': 1})
    board_id = bind.execute(insert).inserted_primary_key[0]
    for index, title in enumerate((u'To Do', u'Doing', u'Done')):
        insert = columns.insert({'title': title,
                                 'index': index,
                                 'board_id': board_id})
        bind.execute(insert)

    for index, (title, color) in enumerate(DEFAULT_LABELS):
        insert = labels.insert({'title': title,
                                'color': color,
                                'index': index,
                                'board_id': board_id})
        bind.execute(insert)


def downgrade():
    op.drop_column('board', 'is_template')
