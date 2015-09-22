# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from elixir import using_options
from elixir import ManyToOne, OneToMany
from elixir import Field, Unicode, Integer, Boolean
from nagare.database import session

from ..card.models import DataCard
from kansha.models import Entity


class DataColumn(Entity):
    """Column mapper
    """
    using_options(tablename='column')
    title = Field(Unicode(200))
    index = Field(Integer)
    nb_max_cards = Field(Integer)
    archive = Field(Boolean, default=False)
    cards = OneToMany('DataCard', order_by='index', cascade='delete')
    board = ManyToOne('DataBoard', colname='board_id')

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
        session.add(col)
        session.flush()
        return col

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

    def reorder(self):
        for i, card in enumerate(self.cards):
            card.index = i

    def get_cards_count(self):
        q = DataCard.query.filter(DataCard.column_id == self.id)
        return q.count()
