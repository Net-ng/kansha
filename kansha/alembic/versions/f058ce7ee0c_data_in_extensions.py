"""Data in extensions

Revision ID: f058ce7ee0c
Revises: 2b0edcfa57b4
Create Date: 2016-01-07 13:41:19.534150

"""

import time
from datetime import date

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f058ce7ee0c'
down_revision = '361f9cbae3fc'


def upgrade():
    bind = op.get_bind()
    is_sqlite = bind.engine.name == 'sqlite'

    op.create_table('card_description',
                    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                    sa.Column('description', sa.UnicodeText, default=lambda: u''),
                    sa.Column('card_id', sa.Integer, sa.ForeignKey('card.id', ondelete='CASCADE')))
    op.create_table('card_due_date',
                    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                    sa.Column('due_date', sa.Date),
                    sa.Column('card_id', sa.Integer, sa.ForeignKey('card.id', ondelete='CASCADE')))
    op.create_table('card_weight',
                    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                    sa.Column('weight', sa.Unicode(255), default=lambda: u''),
                    sa.Column('card_id', sa.Integer, sa.ForeignKey('card.id', ondelete='CASCADE')))
    descriptions = []
    due_dates = []
    weights = []
    descriptions_table = sa.Table(
        'card_description',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('description', sa.UnicodeText, default=lambda: u''),
        sa.Column('card_id', sa.Integer, sa.ForeignKey('card.id', ondelete='CASCADE'))
    )
    due_dates_table = sa.Table(
        'card_due_date',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('due_date', sa.Date),
        sa.Column('card_id', sa.Integer, sa.ForeignKey('card.id', ondelete='CASCADE'))
    )
    weights_table = sa.Table(
        'card_weight',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('weight', sa.Unicode(255), default=lambda: u''),
        sa.Column('card_id', sa.Integer, sa.ForeignKey('card.id', ondelete='CASCADE'))
    )

    select = sa.text('SELECT id, description, due_date, weight FROM card')
    for card_id, description, due_date, weight in bind.execute(select):
        if due_date is not None and is_sqlite:
            due_date = time.strptime(due_date, '%Y-%m-%d')
            due_date = date(due_date.tm_year, due_date.tm_mon, due_date.tm_mday)

        descriptions.append({'card_id': card_id,
                             'description': description})
        due_dates.append({'card_id': card_id,
                          'due_date': due_date})
        weights.append({'card_id': card_id,
                        'weight': weight})

    op.bulk_insert(descriptions_table, descriptions)
    op.bulk_insert(due_dates_table, due_dates)
    op.bulk_insert(weights_table, weights)

    if not is_sqlite: # SQLite doesn't support column dropping
        op.drop_column('card', 'description')
        op.drop_column('card', 'due_date')
        op.drop_column('card', 'weight')


def downgrade():
    op.add_column('card', sa.Column('description', sa.UnicodeText, default=u''))
    op.drop_table('card_description')

    op.add_column('card', sa.Column('due_date', sa.Date))
    op.drop_table('card_due_date')

    op.add_column('card', sa.Column('weight', sa.Unicode(255)))
    op.drop_table('card_weight')
