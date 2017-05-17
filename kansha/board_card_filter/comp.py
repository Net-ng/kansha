# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

# TODO: make it a board extension


class BoardCardFilter(object):

    def __init__(self, card_schema, board_id, exclude_archived, search_engine_service):
        self.card_schema = card_schema
        self.board_id = board_id
        self._exclude_archived = exclude_archived
        self.search_engine = search_engine_service
        self.last_search = ''
        self.card_matches = set()
        # changed by external API call?
        self._changed = False

    def exclude_archived(self, flag):
        self._exclude_archived = flag

    def search(self, query):
        self.last_search = query
        if query:
            condition = self.card_schema.match(query) & (self.card_schema.board_id == self.board_id)
            # do not query archived cards if archive column is hidden
            if self._exclude_archived:
                condition &= (self.card_schema.archived == False)
            self.card_matches = set(doc._id for (_, doc) in self.search_engine.search(condition, 1000))
            # make the difference between empty search and no results
            if not self.card_matches:
                self.card_matches.add(None)
        else:
            self.card_matches = set()

    def reset(self):
        self.last_search = ''
        self.card_matches = set()
        self._changed = True

    def __call__(self, card):
        """Return "highlight" if card matches, "hidden" if it doesn't or "" if
        no filter is active."""
        status = ''
        if self.card_matches:
            status = 'highlight' if card.id in self.card_matches else 'hidden'
        return status

    def reload_search(self):
        if self.last_search:
            self.search(self.last_search)
