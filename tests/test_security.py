# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import unittest
import sys

from nagare import database, i18n, security, component
from nagare.namespaces import xhtml5
from elixir import metadata as __metadata__

from kansha.board import comp as board_module
from kansha.board import boardsmanager
from kansha import helpers
from kansha.security import Unauthorized

database.set_metadata(__metadata__, 'sqlite:///:memory:', False, {})


class BoardTest(unittest.TestCase):

    def setUp(self):
        helpers.setup_db(__metadata__)
        services = helpers.create_services()
        self.boards_manager = boardsmanager.BoardsManager('', '', '', {}, None, services)

    def tearDown(self):
        helpers.teardown_db(__metadata__)

    def test_view_board_1(self):
        """Test security view board 1

        Board Private
        User not logged
        """
        helpers.set_dummy_context()  # to be able to create board
        board = helpers.create_board()
        helpers.set_context()  # real security manager for tests
        self.assertFalse(security.has_permissions('view', board))

    def test_view_board_2(self):
        """Test security view board 2

        Board Public
        User not logged
        """
        helpers.set_dummy_context()  # to be able to create board
        board = helpers.create_board()
        board.set_visibility(board_module.BOARD_PUBLIC)
        user = helpers.create_user('bis')
        helpers.set_context(user)
        self.assertTrue(security.has_permissions('view', board))

    def test_view_board_3(self):
        """Test security view board 3

        Board Private
        User logged but not member of the board
        """
        helpers.set_dummy_context()  # to be able to create board
        board = helpers.create_board()
        board.set_visibility(board_module.BOARD_PRIVATE)
        user = helpers.create_user('bis')
        helpers.set_context(user)
        self.assertFalse(security.has_permissions('view', board))

    def test_view_board_4(self):
        """Test security view board 4

        Board Private
        User member of the board
        """
        helpers.set_dummy_context()  # to be able to create board
        board = helpers.create_board()
        board.set_visibility(board_module.BOARD_PRIVATE)
        user = helpers.create_user('bis')
        helpers.set_context(user)
        board.add_member(user)
        self.assertTrue(security.has_permissions('view', board))

    def test_view_board_5(self):
        """Test security view board 5

        Board Public
        User member of the board
        """
        helpers.set_dummy_context()  # to be able to create board
        board = helpers.create_board()
        board.set_visibility(board_module.BOARD_PUBLIC)
        user = helpers.create_user('bis')
        helpers.set_context(user)
        board.add_member(user)
        self.assertTrue(security.has_permissions('view', board))

    def test_rendering_security_view_board_1(self):
        """Test rendering security view board 1

        Test rendering (Board private / user not logged)
        """
        helpers.set_dummy_context()  # to be able to create board
        board = helpers.create_board()
        board.set_visibility(board_module.BOARD_PRIVATE)
        helpers.set_context()

        with self.assertRaises(Unauthorized):
            component.Component(board).on_answer(lambda x: None).render(xhtml5.Renderer())

    def test_rendering_security_view_board_2(self):
        """Test rendering security view board 2

        Test rendering (Board private / user member)
        """
        # stackless only
        if 'Stackless' not in sys.version:
            return
        helpers.set_dummy_context()  # to be able to create board
        board = helpers.create_board()
        board.set_visibility(board_module.BOARD_PRIVATE)
        user = helpers.create_user('bis')
        helpers.set_context(user)

        board.add_member(user)

        with i18n.Locale('en', 'US'):
            component.Component(board).on_answer(lambda x: None).render(xhtml5.Renderer())

    def test_rendering_security_view_board_3(self):
        """Test rendering security view board 3

        Test rendering (Board public / user not logged)
        """
        helpers.set_dummy_context()  # for board creation
        board = helpers.create_board()
        helpers.set_context()  # for realistic security check
        board.set_visibility(board_module.BOARD_PUBLIC)

        with i18n.Locale('en', 'US'):
            component.Component(board).on_answer(lambda x: None).render(xhtml5.Renderer())
