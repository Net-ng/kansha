# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from nagare import var

from .models import DataHistory


class ActionLog(object):

    def __init__(self, board, card=None):
        self._board = board
        self._card = card

       # View API
        self.user_id = var.Var('')
        self.card_id = var.Var(None)

    @property
    def board(self):
        return self._board

    @property
    def card(self):
        return self._card

    def for_card(self, card):
        """Return new action log restricted to the card.
        The board is the same as self."""
        return ActionLog(self._board, card)

    def add_history(self, user, action, data):
        '''user is App User'''
        DataHistory.add_history(
            self.board.data,
            self.card and self.card.data,
            user.data, action, data
        )

    def delete_card(self):
        if not self._card:
            return
        DataHistory.purge(self._card.data)

    def get_events(self, hours=None):
        return DataHistory.get_events(self.board and self.board.data, hours)

    def get_last_activity(self):
        return DataHistory.get_last_activity(self._board.data)

    @staticmethod
    def get_events_for_data(data_board, hours=None):
        return DataHistory.get_events(data_board, hours)

    # view API
    def get_history(self):
        'internal'
        return DataHistory.get_history(self.board.data, cardid=self.card_id(),
                                       username=self.user_id())


class DummyActionLog(ActionLog):

    def __init__(self):
        super(DummyActionLog, self).__init__(None)

    def add_history(self, user, action, data):
        pass

    def get_last_activity(self):
        return []

    def get_history(self):
        return []
