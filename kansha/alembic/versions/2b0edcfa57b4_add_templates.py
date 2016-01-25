"""Add templates

Revision ID: 2b0edcfa57b4
Revises: 24be36b8c67
Create Date: 2015-11-24 17:50:13.280722

"""

from alembic import op
import elixir
import sqlalchemy as sa

from kansha.board.models import create_template_empty, create_template_todo, DEFAULT_LABELS

# revision identifiers, used by Alembic.
revision = '2b0edcfa57b4'
down_revision = '24be36b8c67'


def upgrade():
    bind = op.get_bind()
    elixir.metadata.bind = bind

    # Add column
    op.add_column('board', sa.Column('is_template', sa.Boolean, default=lambda: False))

    boards = sa.Table('board', elixir.metadata, autoload=True)
    columns = sa.Table('column', elixir.metadata, autoload=True)
    labels = sa.Table('label', elixir.metadata, autoload=True)

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
