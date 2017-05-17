# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from sqlalchemy import func
from elixir import ManyToOne
from elixir import using_options

from nagare.database import session

from kansha.models import Entity


class DataVote(Entity):
    using_options(tablename='vote')
    user = ManyToOne('DataUser', ondelete='CASCADE')
    card = ManyToOne('DataCard', ondelete='CASCADE')

    @classmethod
    def new(cls, card, user):
        """Create and persist."""
        vote = cls(card=card, user=user)
        session.add(vote)
        session.flush()
        return vote

    @classmethod
    def get_vote(cls, card, user):
        '''Return Vote instance which match with user and card

        In:
            - ``card`` -- DataCard instance
            - ``user`` -- DataUser instance
        Return:
            - DataVote instance
        '''
        return cls.get_by(user=user, card=card)

    @classmethod
    def has_voted(cls, card, user):
        '''Return if a user has voted for a given card

        In:
            - ``card`` -- DataCard instance
            - ``user`` -- DataUser instance
        Return:
            - True if a vote is found, False otherwise
        '''
        return cls.get_vote(card, user) is not None

    @classmethod
    def count_votes(cls, card):
        q = cls.query
        q = q.filter(cls.card == card)
        return q.with_entities(func.count()).scalar()

    @classmethod
    def purge(cls, card):
        for vote in cls.query.filter_by(card=card):
            vote.delete()
