# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from collections import OrderedDict

from nagare import security, component, i18n

from kansha import events

from .comp import Board, BOARD_PRIVATE, BOARD_PUBLIC


class BoardsManager(object):
    def __init__(self, app_title, app_banner, theme, card_extensions, search_engine_service, services_service):
        self.app_title = app_title
        self.app_banner = app_banner
        self.theme = theme
        self.card_extensions = card_extensions
        self.search_engine = search_engine_service
        self._services = services_service

        self.last_modified_boards = []
        self.my_boards = []
        self.guest_boards = []
        self.shared_boards = []
        self.archived_boards = []
        self.templates = {}

    def get_by_id(self, id_):
        board = None
        if Board.exists(id=id_):
            return self._services(Board, id_, self.app_title, self.app_banner, self.theme,
                                  self.card_extensions)
        return board

    def get_by_uri(self, uri):
        board = None
        if Board.exists(uri=uri):
            id_ = Board.get_id_by_uri(uri)
            return self._services(Board, id_, self.app_title, self.app_banner, self.theme,
                                  self.card_extensions)
        return board

    def create_board_from_template(self, template_id, user=None):
        if user is None:
            user = security.get_user()
        template = self._services(
            Board, template_id, self.app_title, self.app_banner, self.theme,
            self.card_extensions)
        new_board = template.copy(user)
        new_board.archive_column = new_board.create_column(index=-1, title=i18n._(u'Archive'))
        new_board.archive_column.is_archive = True
        new_board.mark_as_template(False)
        return new_board

    def create_template_from_board(self, board, title, description, shared, user=None):
        if user is None:
            user = security.get_user()
        template = board.copy(user)
        template.mark_as_template()
        template.set_title(title)
        template.set_description(description)
        template.set_visibility(BOARD_PRIVATE if not shared else BOARD_PUBLIC)
        return template

    def load_user_boards(self):
        user = security.get_user()
        self.my_boards = []
        self.guest_boards = []
        self.archived_boards = []
        last_modifications = set()
        for board_obj in self._services(Board.get_all_boards, user, self.app_title,
                                        self.app_banner, self.theme,
                                        self.card_extensions,
                                        load_children=False):
            if (security.has_permissions('manage', board_obj) or
                    security.has_permissions('edit', board_obj)):
                board_comp = component.Component(board_obj)
                if board_obj.archived:
                    self.archived_boards.append(board_comp)
                else:
                    last_activity = board_obj.get_last_activity()
                    if last_activity is not None:
                        last_modifications.add((last_activity, board_comp))
                    if security.has_permissions('manage', board_obj):
                        self.my_boards.append(board_comp)
                    elif security.has_permissions('edit', board_obj):
                        self.guest_boards.append(board_comp)

        last_5 = sorted(last_modifications, reverse=True)[:5]
        self.last_modified_boards = [comp for _modified, comp in last_5]

        self.shared_boards = [
            component.Component(board_obj) for board_obj in
            self._services(Board.get_shared_boards, self.app_title,
                           self.app_banner, self.theme,
                           self.card_extensions,
                           load_children=False)
        ]

        public, private = Board.get_templates_for(user)
        self.templates = {'public': [(b.id, b.template_title) for b in public],
                          'private': [(b.id, b.template_title) for b in private]}

    def purge_archived_boards(self):
        for board in self.archived_boards:
            board().load_children()
            board().delete()
        self.load_user_boards()

    def handle_event(self, event):
        if event.is_kind_of(events.BoardAccessChanged):
            if event.is_(events.BoardDeleted):
                board = event.emitter
                board.load_children()
                board.delete()
            return self.load_user_boards()

    #####

    def create_board(self, board_id, comp):
        """Create a new board from template for current user."""
        new_board = self.create_board_from_template(board_id)
        comp.answer(new_board.id)

