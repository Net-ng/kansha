"""membership

Revision ID: 25739bc150b9
Revises: 2c0a3788227
Create Date: 2017-01-13 17:58:55.516698

"""
import elixir
from alembic import op
import sqlalchemy as sa
from nagare.database import session

from kansha.card.models import DataCard
from kansha.card_addons.members.models import DataMembership, DataCardMembership


# revision identifiers, used by Alembic.
revision = '25739bc150b9'
down_revision = '2c0a3788227'

def upgrade():
    bind = op.get_bind()
    session.bind = bind
    elixir.metadata.bind = bind
    elixir.setup_all()
    elixir.create_all()

    members = {}

    select = sa.text('SELECT board_id, user_username, user_source FROM user_managed_boards__board_managers')
    for board_id, username, source in bind.execute(select):
        key = (username, source, board_id)
        members[key] = DataMembership(board_id=board_id, user_username=username, user_source=source, manager=True, notify=0)

    select = sa.text('SELECT board_id, user_username, user_source, notify FROM user_boards__board_members')
    for board_id, username, source, notify in bind.execute(select):
        key = (username, source, board_id)
        if key not in members:
            members[key] = DataMembership(board_id=board_id, user_username=username, user_source=source, manager=False, notify=notify)
        else:
            members[key].notify = notify
    print sorted(members.keys())
    select = sa.text('SELECT card_id, user_username, user_source FROM user_cards__card_members')
    for card_id, username, source in bind.execute(select):
        card = DataCard.get(card_id)
        member = members.get((username, source, card.column.board_id))
        if member:
            member.card_memberships.append(DataCardMembership(card=card))
        else:
            print 'illegal member', username, 'on card', card.title

    op.drop_table('user_cards__card_members')
    op.drop_table('user_boards__board_members')
    op.drop_table('user_managed_boards__board_managers')


def downgrade():
    bind = op.get_bind()
    session.bind = bind
    elixir.metadata.bind = bind
    elixir.setup_all()
    elixir.create_all()
    op.drop_table('membership')
