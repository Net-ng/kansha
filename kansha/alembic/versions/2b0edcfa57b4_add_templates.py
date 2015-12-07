"""Add templates

Revision ID: 2b0edcfa57b4
Revises: 24be36b8c67
Create Date: 2015-11-24 17:50:13.280722

"""

from alembic import op
import elixir
import sqlalchemy as sa

from kansha.board.models import create_template_empty, create_template_todo

# revision identifiers, used by Alembic.
revision = '2b0edcfa57b4'
down_revision = '24be36b8c67'

def upgrade():
    # Add column
    op.add_column('board', sa.Column('is_template', sa.Boolean, default=False))

    # Setup models
    elixir.metadata.bind = op.get_bind()
    elixir.setup_all()

    # Create default template
    create_template_empty()
    create_template_todo()


def downgrade():
    op.drop_column('board', 'is_template')
