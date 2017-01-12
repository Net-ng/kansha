#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import database
from sqlalchemy import func
from elixir import ManyToOne, ManyToMany, using_options

from kansha.models import Entity
from kansha.card.models import DataCard
from kansha.user.models import DataUser
from kansha.column.models import DataColumn


class DataMembership(Entity):
    using_options(tablename='user_cards__card_members')

    user = ManyToOne(DataUser, primary_key=True)
    card = ManyToOne(DataCard, primary_key=True)

    @classmethod
    def get_for_card(cls, card):
        return cls.query.filter_by(card=card)

    @staticmethod
    def favorites_for(card):
        query = database.session.query(DataUser)
        query = query.join(DataMembership)
        query = query.join(DataCard).join(DataColumn).filter(DataColumn.board == card.column.board)
        query = query.group_by(DataUser.username, DataUser.source)
        query = query.order_by(func.count(DataUser.username).desc())
        return query

    @classmethod
    def add_members_from_emails(cls, card, emails):
        memberships = []
        for user in map(DataUser.get_by_email, emails):
            membership = cls(user=user, card=card)
            database.session.add(membership)
            memberships.append(membership)
        database.session.flush()
        return memberships

    @classmethod
    def remove_member(cls, card, username):
        user = DataUser.get_by_username(username)
        if user:
            membership = DataMembership.get((user, card))
            if membership:
                membership.delete()
