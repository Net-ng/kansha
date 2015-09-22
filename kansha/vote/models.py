# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from elixir import using_options
from elixir import ManyToOne

from kansha.models import Entity


class DataVote(Entity):
    using_options(tablename='vote')
    user = ManyToOne('DataUser')
    card = ManyToOne('DataCard')

    @classmethod
    def get_vote(cls, user, card):
        """Return Vote instance which match with user and card

        In:
            - ``user`` -- DataUser instance
            - ``card`` -- DataCard instance
        Return:
            - DataVote instance
        """
        q = cls.query
        q = q.filter(cls.user == user)
        q = q.filter(cls.card == card)
        return q.one()
