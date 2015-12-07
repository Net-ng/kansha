# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from .comp import Board


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

    def copy_board(self, board, user, board_to_template=True):
        data = {}
        new_board = board.copy(user, data)
        new_board.data.is_template = board_to_template
        return new_board
