# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from datetime import datetime

from sqlalchemy import func
from elixir import using_options
from elixir import ManyToOne, OneToMany
from elixir import Field, Unicode, Integer, Boolean
from sqlalchemy.ext.orderinglist import ordering_list

from nagare.database import session

from kansha.card.models import DataCard
from kansha.models import Entity


class DataColumn(Entity):
    """Column mapper
    """
    using_options(tablename='column')
    title = Field(Unicode(200))
    index = Field(Integer)
    nb_max_cards = Field(Integer)
    archive = Field(Boolean, default=False)
    cards = OneToMany('DataCard', order_by='index',  # cascade='delete',
                      collection_class=ordering_list('index'), lazy='subquery')
    board = ManyToOne('DataBoard', colname='board_id')

    def update(self, other):
        self.title = other.title
        self.index = other.index
        self.nb_max_cards = other.nb_max_cards
        session.flush()

    @classmethod
    def create_column(cls, board, index, title, nb_cards=None, archive=False):
        """Create new column

        In:
            - ``board`` -- DataBoard, father of the column
            - ``index`` -- position in the board
            - ``title`` -- title of the column
        Return:
            - created DataColumn instance
        """
        q = cls.query
        q = q.filter(cls.index >= index)
        q = q.filter(cls.board == board)
        q.update({'index': cls.index + 1})
        col = cls(title=title, index=index, board=board, nb_max_cards=nb_cards, archive=archive)
        # session.add(col)
        session.flush()
        return col

    def create_card(self, title, user):
        card = DataCard(title=title, creation_date=datetime.now())
        self.cards.append(card)
        session.flush()
        return card

    def remove_card(self, card):
        if card in self.cards:
            self.cards.remove(card)

    def insert_card(self, index, card):
        done = False
        if card not in self.cards:
            self.cards.insert(index, card)
            session.flush()
            done = True
        return done

    def delete_card(self, card):
        self.remove_card(card)
        card.delete()

    def purge_cards(self):
        for card in self.cards:
            card.delete()

    def append_card(self, card):
        done = False
        if card not in self.cards:
            card.index = None
            self.cards.append(card)
            session.flush()
            done = True
        return done

    @classmethod
    def delete_column(cls, column):
        """Delete column

        Delete a given column, re-index other columns and delete all cards
        of the column

        In:
            - ``column`` -- DataColumn instance to delete
        """
        index = column.index
        board = column.board
        column.delete()
        session.flush()
        q = cls.query
        q = q.filter(cls.index >= index)
        q = q.filter(cls.board == board)
        q.update({'index': cls.index - 1})

    def get_cards_count(self):
        q = DataCard.query.filter(DataCard.column_id == self.id)
        return q.with_entities(func.count()).scalar()
