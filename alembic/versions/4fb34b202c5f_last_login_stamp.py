"""last_login stamp

Revision ID: 4fb34b202c5f
Revises: 6cb3c668d65
Create Date: 2015-05-18 19:00:56.564336

"""

# revision identifiers, used by Alembic.
revision = '4fb34b202c5f'
down_revision = '6cb3c668d65'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('last_login', sa.DateTime))


def downgrade():
    op.drop_column('user', 'last_login')
