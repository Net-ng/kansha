"""email index

Revision ID: 55f89221fc55
Revises: 25739bc150b9
Create Date: 2017-01-24 16:44:02.500510

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '55f89221fc55'
down_revision = '25739bc150b9'


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_email_to_confirm'), ['email_to_confirm'], unique=True)


def downgrade():
    pass
