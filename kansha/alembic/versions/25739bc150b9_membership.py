"""membership

Revision ID: 25739bc150b9
Revises: 2c0a3788227
Create Date: 2017-01-13 17:58:55.516698

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '25739bc150b9'
down_revision = '2c0a3788227'

def upgrade():
    bind = op.get_bind()

    members = {}

    # gather board memberships
    select = sa.text('SELECT board_id, user_username, user_source FROM user_managed_boards__board_managers')
    for board_id, username, source in bind.execute(select):
        key = (username, source, board_id)
        members[key] = dict(board_id=board_id, user_username=username, user_source=source, manager=True, notify=0)

    select = sa.text('SELECT board_id, user_username, user_source, notify FROM user_boards__board_members')
    for board_id, username, source, notify in bind.execute(select):
        key = (username, source, board_id)
        if key not in members:
            members[key] = dict(board_id=board_id, user_username=username, user_source=source, manager=False, notify=notify)
        else:
            members[key]['notify'] = notify
    print sorted(members.keys())

    # Create unified membership table
    op.create_table(
        'membership',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('board_id', sa.Integer, sa.ForeignKey('board.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_username', sa.Unicode, nullable=False),
        sa.Column('user_source', sa.Unicode, nullable=False),
        sa.Column('manager', sa.Boolean, default=False, nullable=False),
        sa.Column('notify', sa.Integer, default=1),
        sa.ForeignKeyConstraint(['user_username', 'user_source'], ['user.username', 'user.source'], ondelete='CASCADE'),
        sa.UniqueConstraint('board_id', 'user_username', 'user_source', name='membership_ix')
    )
    membership = sa.Table(
        'membership',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('board_id', sa.Integer, sa.ForeignKey('board.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_username', sa.Unicode, nullable=False),
        sa.Column('user_source', sa.Unicode, nullable=False),
        sa.Column('manager', sa.Boolean, default=False, nullable=False),
        sa.Column('notify', sa.Integer, default=1),
        sa.ForeignKeyConstraint(['user_username', 'user_source'], ['user.username', 'user.source'], ondelete='CASCADE'),
        sa.UniqueConstraint('board_id', 'user_username', 'user_source', name='membership_ix')
    )
    # migrate the data
    op.bulk_insert(membership, members.values())
    # Keep track of ids
    for ms in bind.execute(membership.select()):
        members[(ms.user_username, ms.user_source, ms.board_id)]['membership'] = ms.id

    # Create card membership table
    op.create_table(
        'membership_cards__card',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('membership_id', sa.Integer, sa.ForeignKey('membership.id', ondelete='CASCADE'), nullable=False),
        sa.Column('card_id', sa.Integer, sa.ForeignKey('card.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('membership_id', 'card_id', name='card_membership_ix')
    )

    card_membership = sa.Table(
        'membership_cards__card',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('membership_id', sa.Integer, sa.ForeignKey('membership.id', ondelete='CASCADE'), nullable=False),
        sa.Column('card_id', sa.Integer, sa.ForeignKey('card.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('membership_id', 'card_id', name='card_membership_ix')
    )
    # gather card membership information
    card_members = []
    select = sa.text("SELECT cm.card_id, cm.user_username, cm.user_source, col.board_id "
                     "FROM user_cards__card_members as cm join card on cm.card_id = card.id "
                     'join "column" as col on card.column_id = col.id')
    for card_id, username, source, board_id in bind.execute(select):
        member = members.get((username, source, board_id))
        if member:
            card_members.append(dict(card_id=card_id, membership_id=member['membership']))
        else:
            print 'illegal member', username, 'on card', card_id
    # migrate the data
    op.bulk_insert(card_membership, card_members)

    op.drop_table('user_cards__card_members')
    op.drop_table('user_boards__board_members')
    op.drop_table('user_managed_boards__board_managers')


def downgrade():
    print 'There is no way back...'