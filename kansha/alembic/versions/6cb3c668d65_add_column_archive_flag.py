"""Add column archive flag

Revision ID: 6cb3c668d65
Revises: 36d972f11e3e
Create Date: 2014-03-03 16:07:47.321713

"""

# revision identifiers, used by Alembic.
revision = '6cb3c668d65'
down_revision = '36d972f11e3e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('column', sa.Column('archive', sa.Boolean, server_default='false'))
    op.add_column('board', sa.Column('archive', sa.Integer, server_default='0'))
    op.add_column('board', sa.Column('archived', sa.Boolean, server_default='false'))
    op.add_column('board', sa.Column('weighting_cards', sa.Integer, server_default='0'))
    op.add_column('board', sa.Column('weights', sa.Text, server_default=''))
    op.add_column('card', sa.Column('weight', sa.Text, server_default=''))


def downgrade():
    op.drop_column('column', 'archive')
    op.drop_column('board', 'archive')
    op.drop_column('board', 'archived')
    op.drop_column('board', 'weighting_cards')
    op.drop_column('board', 'weights')
    op.drop_column('card', 'weight')
