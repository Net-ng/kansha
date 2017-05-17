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
from elixir import ManyToOne, ManyToMany
from elixir import Field, Unicode, Integer

from kansha.models import Entity


class DataLabel(Entity):

    """Label mapper
    """
    using_options(tablename='label')
    title = Field(Unicode(255))
    color = Field(Unicode(255))
    board = ManyToOne('DataBoard')
    cards = ManyToMany('DataCard', tablename='label_cards__card_labels')
    index = Field(Integer)

    def copy(self):
        new_data = DataLabel(title=self.title,
                             color=self.color,
                             index=self.index)
        return new_data

    def remove(self, card):
        self.cards.remove(card)

    def add(self, card):
        self.cards.append(card)

    @classmethod
    def get_by_card(cls, card):
        q = cls.query
        q = q.filter(cls.cards.contains(card))
        return q.order_by(cls.index)
