"""Add templates

Revision ID: 2b0edcfa57b4
Revises: 24be36b8c67
Create Date: 2015-11-24 17:50:13.280722

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '2b0edcfa57b4'
down_revision = '24be36b8c67'

def upgrade():
    op.add_column('board', sa.Column('is_template', sa.Boolean, default=False))


def downgrade():
    op.drop_column('board', 'is_template')
