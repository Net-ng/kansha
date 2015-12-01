"""Add templates

Revision ID: 2b0edcfa57b4
Revises: 24be36b8c67
Create Date: 2015-11-24 17:50:13.280722

"""

from alembic import op
import elixir
import sqlalchemy as sa

from nagare import local, security

from kansha.board.boardsmanager import BoardsManager
from kansha.security import SecurityManager
from kansha.services.dummyassetsmanager.dummyassetsmanager import DummyAssetsManager
from kansha.services.services_repository import ServicesRepository
from kansha.services.mail import DummyMailSender

# revision identifiers, used by Alembic.
revision = '2b0edcfa57b4'
down_revision = '24be36b8c67'

def upgrade():
    # Setup models
    elixir.metadata.bind = op.get_bind()
    elixir.setup_all()

    # Add column
    op.add_column('board', sa.Column('is_template', sa.Boolean, default=False))

    # Create default template
    local.request = local.Thread()
    security.set_manager(SecurityManager(''))

    services = ServicesRepository()
    services.register('assets_manager', DummyAssetsManager())
    services.register('mail_sender', DummyMailSender())

    bm = BoardsManager('', '', '', {}, None, services)
    bm.create_template_todo()


def downgrade():
    op.drop_column('board', 'is_template')
