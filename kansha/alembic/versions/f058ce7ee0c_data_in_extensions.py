"""Data in extensions

Revision ID: f058ce7ee0c
Revises: 2b0edcfa57b4
Create Date: 2016-01-07 13:41:19.534150

"""

import time
from datetime import date

import elixir
from alembic import op
import sqlalchemy as sa
from nagare.database import session

from kansha.card_addons.weight.models import DataCardWeight
from kansha.card_addons.due_date.models import DataCardDueDate
from kansha.card_addons.description.models import DataCardDescription


# revision identifiers, used by Alembic.
revision = 'f058ce7ee0c'
down_revision = '361f9cbae3fc'

def upgrade():
    bind = op.get_bind()
    session.bind = bind
    elixir.metadata.bind = bind
    elixir.setup_all()
    elixir.create_all()
    is_sqlite = bind.engine.name == 'sqlite'

    select = sa.text('SELECT id, description, due_date, weight FROM card')
    for card_id, description, due_date, weight in bind.execute(select):
        if due_date is not None and is_sqlite:
            due_date = time.strptime(due_date, '%Y-%m-%d')
            due_date = date(due_date.tm_year, due_date.tm_mon, due_date.tm_mday)
        DataCardDescription(card_id=card_id, description=description)
        DataCardDueDate(card_id=card_id, due_date=due_date)
        DataCardWeight(card_id=card_id, weight=weight)

    session.flush()

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
