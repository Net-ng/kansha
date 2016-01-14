# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from elixir import ManyToOne
from elixir import using_options
from elixir import Field, Unicode
from nagare.database import session


from kansha.models import Entity


class DataCardWeight(Entity):
    using_options(tablename='card_weight')

    weight = Field(Unicode(255), default=u'')
    card = ManyToOne('DataCard', ondelete='cascade')

    def update(self, other):
        self.weight = other.weight
        session.flush()

    @classmethod
    def get_by_card(cls, card):
        q = cls.query
        q = q.filter_by(card=card)
        return q.first()