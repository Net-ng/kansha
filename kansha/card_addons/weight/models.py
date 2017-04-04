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
from elixir import Field, Integer, Unicode
from nagare.database import session


from kansha.models import Entity


class DataBoardWeightConfig(Entity):
    using_options(tablename='board_weight_config')

    board = ManyToOne('DataBoard', ondelete='cascade')

    weighting_cards = Field(Integer, default=0)
    weights = Field(Unicode(255), default=u'0, 1, 2, 3, 5, 8, 13')


class DataCardWeight(Entity):
    using_options(tablename='card_weight')

    weight = Field(Integer, default=0)
    card = ManyToOne('DataCard', ondelete='cascade')

    def update(self, other):
        self.weight = other.weight
        session.flush()

    @classmethod
    def get_by_card(cls, card):
        q = cls.query
        q = q.filter_by(card=card)
        return q.first()