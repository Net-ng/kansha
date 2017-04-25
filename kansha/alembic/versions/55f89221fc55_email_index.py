"""email index

Revision ID: 55f89221fc55
Revises: 25739bc150b9
Create Date: 2017-01-24 16:44:02.500510

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import and_

# revision identifiers, used by Alembic.
revision = '55f89221fc55'
down_revision = '25739bc150b9'


users = sa.Table(
    'user',
    sa.MetaData(),
    sa.Column('username', sa.VARCHAR(255), primary_key=True),
    sa.Column('source', sa.VARCHAR(255), primary_key=True),
    sa.Column('email', sa.Unicode),
    sa.Column('email_to_confirm', sa.Unicode),
    sa.Column('registration_date', sa.DateTime)
)

membership = sa.Table(
    'membership',
    sa.MetaData(),
    sa.Column('user_username', sa.Unicode, nullable=False),
    sa.Column('user_source', sa.Unicode, nullable=False),
)

vote = sa.Table(
    'vote',
    sa.MetaData(),
    sa.Column('user_username', sa.Unicode, nullable=False),
    sa.Column('user_source', sa.Unicode, nullable=False)
)

history = sa.Table(
    'history',
    sa.MetaData(),
    sa.Column('user_username', sa.Unicode, nullable=False),
    sa.Column('user_source', sa.Unicode, nullable=False)
)

checklist = sa.Table(
    'checklists',
    sa.MetaData(),
    sa.Column('author_username', sa.Unicode, nullable=False),
    sa.Column('author_source', sa.Unicode, nullable=False)
)

comment = sa.Table(
    'comment',
    sa.MetaData(),
    sa.Column('author_username', sa.Unicode, nullable=False),
    sa.Column('author_source', sa.Unicode, nullable=False)
)

asset = sa.Table(
    'asset',
    sa.MetaData(),
    sa.Column('author_username', sa.Unicode, nullable=False),
    sa.Column('author_source', sa.Unicode, nullable=False)
)

card = sa.Table(
    'card',
    sa.MetaData(),
    sa.Column('author_username', sa.Unicode, nullable=False),
    sa.Column('author_source', sa.Unicode, nullable=False)
)

board = sa.Table(
    'board',
    sa.MetaData(),
    sa.Column('last_users_username', sa.Unicode, nullable=False),
    sa.Column('last_users_source', sa.Unicode, nullable=False)
)


def merge_users(bind, old_user, new_user):
    print "merging", old_user, 'into', new_user
    bind.execute(
        membership.update().where(
            and_(
                membership.c.user_username == old_user.username,
                membership.c.user_source == old_user.source
            )
        ).values(
            user_username=new_user.username,
            user_source=new_user.source
        )
    )
    bind.execute(
        vote.update().where(
            and_(
                vote.c.user_username == old_user.username,
                vote.c.user_source == old_user.source
            )
        ).values(
            user_username=new_user.username,
            user_source=new_user.source
        )
    )
    bind.execute(
        history.update().where(
            and_(
                history.c.user_username == old_user.username,
                history.c.user_source == old_user.source
            )
        ).values(
            user_username=new_user.username,
            user_source=new_user.source
        )
    )
    bind.execute(
        comment.update().where(
            and_(
                comment.c.author_username == old_user.username,
                comment.c.author_source == old_user.source
            )
        ).values(
            author_username=new_user.username,
            author_source=new_user.source
        )
    )
    bind.execute(
        checklist.update().where(
            and_(
                checklist.c.author_username == old_user.username,
                checklist.c.author_source == old_user.source
            )
        ).values(
            author_username=new_user.username,
            author_source=new_user.source
        )
    )
    bind.execute(
        asset.update().where(
            and_(
                asset.c.author_username == old_user.username,
                asset.c.author_source == old_user.source
            )
        ).values(
            author_username=new_user.username,
            author_source=new_user.source
        )
    )
    bind.execute(
        card.update().where(
            and_(
                card.c.author_username == old_user.username,
                card.c.author_source == old_user.source
            )
        ).values(
            author_username=new_user.username,
            author_source=new_user.source
        )
    )
    bind.execute(
        board.update().where(
            and_(
                board.c.last_users_username == old_user.username,
                board.c.last_users_source == old_user.source
            )
        ).values(
            last_users_username=new_user.username,
            last_users_source=new_user.source
        )
    )


def upgrade():
    # first, find and merge duplicates
    # then, set unique index
    bind = op.get_bind()
    select = sa.text('select email from "user" where email is not null group by email having count(*) > 1')
    for email in bind.execute(select):
        same_users = bind.execute(users.select().where(users.c.email == email[0]).order_by('registration_date')).fetchall()
        kept_user = same_users.pop()
        for obsolete_user in same_users:
            merge_users(bind, obsolete_user, kept_user)
            bind.execute(users.delete().where(
                and_(
                    users.c.username == obsolete_user.username,
                    users.c.source == obsolete_user.source)))
    # phantom users, lost forever...
    bind.execute(users.update().where(users.c.email == None).values(email_to_confirm=None))
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_email_to_confirm'), ['email_to_confirm'], unique=True)


def downgrade():
    pass
