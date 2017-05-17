"""weights are numbers

Revision ID: 443501b69d16
Revises: 55f89221fc55
Create Date: 2017-04-03 18:28:50.108072

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '443501b69d16'
down_revision = '55f89221fc55'


def upgrade():
    bind = op.get_bind()
    op.create_table('board_weight_config',
                    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                    sa.Column('weights', sa.Unicode(255), default=u'0, 1, 2, 3, 5, 8, 13'),
                    sa.Column('weighting_cards', sa.Integer, default=0),
                    sa.Column('board_id', sa.Integer, sa.ForeignKey('board.id', ondelete='CASCADE')))
    # collect existing weights
    weights = {}
    select = sa.text('SELECT card_id, weight FROM card_weight')
    for card_id, weight in bind.execute(select):
        weights[card_id] = int(weight or 0)
    op.drop_column('card_weight', 'weight')

    # data migration
    op.add_column('card_weight', sa.Column('weight', sa.Integer))
    weights_table = sa.Table(
        'card_weight',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('weight', sa.Integer, default=0),
        sa.Column('card_id', sa.Integer, sa.ForeignKey('card.id', ondelete='CASCADE'))
    )
    for card_id, weight in weights.iteritems():
        bind.execute(
            weights_table.update().where(
                weights_table.c.card_id == card_id
            ).values(
                weight=weight
            )
        )
    board_weight_config = sa.Table(
        'board_weight_config',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('weights', sa.Unicode(255), default=u'0, 1, 2, 3, 5, 8, 13'),
        sa.Column('weighting_cards', sa.Integer, default=0),
        sa.Column('board_id', sa.Integer, sa.ForeignKey('board.id', ondelete='CASCADE')))

    board = sa.Table(
        'board',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('weights', sa.Unicode(255), default=u'0, 1, 2, 3, 5, 8, 13'),
        sa.Column('weighting_cards', sa.Integer, default=0),
    )
    conf = [
        dict(weights=board_conf.weights or u'0, 1, 2, 3, 5, 8, 13', weighting_cards=board_conf.weighting_cards, board_id=board_conf.id)
        for board_conf in bind.execute(board.select())
    ]
    op.bulk_insert(board_weight_config, conf)
    # cleaning
    op.drop_column('board', 'weights')
    op.drop_column('board', 'weighting_cards')


def downgrade():
    print "there is no way back!"
