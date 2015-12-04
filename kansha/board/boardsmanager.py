# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
import json
import time
import os.path
from datetime import date, datetime, timedelta
from glob import glob

from nagare import database

from kansha.card.fts_schema import Card as FTSCard
from kansha.card.models import DataCard
from kansha.column.models import DataColumn
from kansha.comment.models import DataComment
from kansha.label.models import DataLabel
from kansha.vote.models import DataVote
from .comp import Board, BOARD_PUBLIC
from .models import DataBoard


DEFAULT_LABELS = (
    (u'Green', u'#22C328'),
    (u'Red', u'#CC3333'),
    (u'Blue', u'#3366CC'),
    (u'Yellow', u'#D7D742'),
    (u'Orange', u'#DD9A3C'),
    (u'Purple', u'#8C28BD')
)


class BoardsManager(object):
    def __init__(self, app_title, app_banner, theme, card_extensions, search_engine, services_service):
        self.app_title = app_title
        self.app_banner = app_banner
        self.theme = theme
        self.card_extensions = card_extensions
        self.search_engine = search_engine
        self._services = services_service

    def get_by_id(self, id_):
        board = None
        if Board.exists(id=id_):
            return self._services(Board, id_, self.app_title, self.app_banner, self.theme,
                                  self.card_extensions, self.search_engine)
        return board

    def get_by_uri(self, uri):
        board = None
        if Board.exists(uri=uri):
            id_ = Board.get_id_by_uri(uri)
            return self._services(Board, id_, self.app_title, self.app_banner, self.theme,
                                  self.card_extensions, self.search_engine)
        return board

    def _get_board(self, data_board):
        '''Build a board object'''
        return self._services(Board, data_board.id, self.app_title, self.app_banner, self.theme,
                              self.card_extensions, self.search_engine)

    def create_template_empty(self):
        '''Get a default empty template'''
        board = DataBoard(title=u'Empty board', is_template=True)
        board.visibility = BOARD_PUBLIC
        for i, (title, color) in enumerate(DEFAULT_LABELS):
            board.labels.append(DataLabel(title=title, color=color, index=i))
        database.session.flush()
        return self._get_board(board)

    def create_template_todo(self):
        '''Get a default Todo template'''
        board = DataBoard(title=u'Todo', is_template=True)
        board.visibility = BOARD_PUBLIC
        for index, title in enumerate((u'To Do', u'Doing', u'Done')):
            board.create_column(index, title)
        for i, (title, color) in enumerate(DEFAULT_LABELS):
            board.labels.append(DataLabel(title=title, color=color, index=i))
        database.session.flush()
        return self._get_board(board)

    def copy_board(self, board, user, board_to_template=True):
        data = {}
        new_board = board.copy(user, data)
        new_board.data.is_template = board_to_template
        return new_board

    @staticmethod
    def index_user_cards(user, search_engine):
        for card in user.my_cards:
            search_engine.add_document(FTSCard.from_model(card))
        search_engine.commit()
