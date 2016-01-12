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
from nagare.database import session

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

    def copy(self, parent):
        new_data = DataLabel(title=self.title,
                             color=self.color,
                             index=self.index,
                             board=parent)
        session.flush()
        return new_data

    @classmethod
    def get_by_card(cls, card):
        q = cls.query
        q = q.filter(cls.cards.contains(card))
        return q.all()

    @classmethod
    def add_to_card(cls, card, id):
        label = cls.get(id)
        if not card in label.cards:
            label.cards.append(card)

    @classmethod
    def remove_from_card(cls, card, id):
        label = cls.get(id)
        if card in label.cards:
            label.cards.remove(card)
