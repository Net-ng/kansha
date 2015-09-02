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
from nagare import database
from sqlalchemy import MetaData
from kansha.board.models import DataBoard
from kansha.board import comp as board_module
from kansha.board import boardsmanager
from . import helpers
from elixir import metadata as __metadata__

database.set_metadata(__metadata__, 'sqlite:///:memory:', False, {})


class BoardTest(unittest.TestCase):

    def setUp(self):
        helpers.setup_db(__metadata__)
        self.boards_manager = boardsmanager.BoardsManager()

    def tearDown(self):
        helpers.teardown_db(__metadata__)

    def test_add_board(self):
        """Create a new board"""
        helpers.set_dummy_context()
        self.assertEqual(DataBoard.query.count(), 0)
        user = helpers.create_user()
        helpers.set_context(user)
        self.boards_manager.create_board(helpers.word(), user)
        self.assertEqual(DataBoard.query.count(), 1)

    def test_add_column_ok(self):
        """Add a column to a board"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        assert (board.archive_column is not None)
        self.assertEqual(board.count_columns(), 3)
        board.create_column(0, helpers.word())
        self.assertEqual(board.count_columns(), 4)

    def test_add_column_ko(self):
        """Add a column with empty title to a board"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        self.assertEqual(board.count_columns(), 3)
        self.assertEqual(board.create_column(0, ''), False)

    def test_delete_column(self):
        """Delete column from a board"""
        helpers.set_dummy_context()
        user = helpers.create_user()
        helpers.set_context(user)
        board = helpers.create_board()
        assert (board.archive_column is not None)
        self.assertEqual(board.count_columns(), 3)
        column_id = board.columns[0]().db_id
        board.delete_column(column_id)
        self.assertEqual(board.count_columns(), 2)

    def test_move_cards(self):
        """Test move cards"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        self.assertEqual(len(board.columns), 3)
        move_cards_value = """[
            ["list_2", ["card_10", "card_1", "card_3", "card_5"]],
            ["list_1", ["card_7", "card_2", "card_8", "card_11"]],
            ["list_3", ["card_6", "card_4", "card_9"]]]"""
        # This has the side effect of implicitly hiding the archive
        # because it is not present in above values
        board.move_cards(move_cards_value)
        # Test columns
        self.assertEqual(len(board.data.columns), 4)
        self.assertEqual(len(board.columns), 3)
        self.assertEqual(board.data.columns[0].id, 2)
        self.assertEqual(board.columns[0]().id, "list_2")
        self.assertEqual(board.data.columns[1].id, 1)
        self.assertEqual(board.columns[1]().id, "list_1")
        self.assertEqual(board.data.columns[2].id, 3)
        self.assertEqual(board.columns[2]().id, "list_3")

        # Test cards
        self.assertEqual(len(board.data.columns[0].cards), 4)
        self.assertEqual(len(board.columns[0]().cards), 4)
        self.assertEqual(board.data.columns[0].cards[0].id, 10)
        self.assertEqual(board.columns[0]().cards[0]().id, 'card_10')
        self.assertEqual(board.data.columns[0].cards[1].id, 1)
        self.assertEqual(board.columns[0]().cards[1]().id, 'card_1')
        self.assertEqual(board.data.columns[0].cards[2].id, 3)
        self.assertEqual(board.columns[0]().cards[2]().id, 'card_3')
        self.assertEqual(board.data.columns[0].cards[3].id, 5)
        self.assertEqual(board.columns[0]().cards[3]().id, 'card_5')
        self.assertEqual(len(board.data.columns[1].cards), 4)
        self.assertEqual(len(board.columns[1]().cards), 4)
        self.assertEqual(board.data.columns[1].cards[0].id, 7)
        self.assertEqual(board.columns[1]().cards[0]().id, 'card_7')
        self.assertEqual(board.data.columns[1].cards[1].id, 2)
        self.assertEqual(board.columns[1]().cards[1]().id, 'card_2')
        self.assertEqual(board.data.columns[1].cards[2].id, 8)
        self.assertEqual(board.columns[1]().cards[2]().id, 'card_8')
        self.assertEqual(board.data.columns[1].cards[3].id, 11)
        self.assertEqual(board.columns[1]().cards[3]().id, 'card_11')
        self.assertEqual(len(board.data.columns[2].cards), 3)
        self.assertEqual(len(board.columns[2]().cards), 3)
        self.assertEqual(board.data.columns[2].cards[0].id, 6)
        self.assertEqual(board.columns[2]().cards[0]().id, 'card_6')
        self.assertEqual(board.data.columns[2].cards[1].id, 4)
        self.assertEqual(board.columns[2]().cards[1]().id, 'card_4')
        self.assertEqual(board.data.columns[2].cards[2].id, 9)
        self.assertEqual(board.columns[2]().cards[2]().id, 'card_9')

    def test_set_visibility_1(self):
        """Test set visibility method 1

        Initial State:
         - board:private
         - allow_comment: off
         - allow_votes: members

        End state
         - board:public
         - allow_comment: off
         - allow_votes: members
        """
        helpers.set_dummy_context()
        board = helpers.create_board()
        board.data.visibility = 0
        board.data.comments_allowed = 0
        board.data.votes_allowed = 1

        board.set_visibility(board_module.BOARD_PUBLIC)

        self.assertEqual(board.data.visibility, 1)
        self.assertEqual(board.data.comments_allowed, 0)
        self.assertEqual(board.data.votes_allowed, 1)

    def test_set_visibility_2(self):
        """Test set visibility method 2

        Initial State:
         - board:public
         - allow_comment: public
         - allow_votes: public

        End state
         - board:private
         - allow_comment: members
         - allow_votes: members
        """
        helpers.set_dummy_context()
        board = helpers.create_board()
        board.data.visibility = 1
        board.data.comments_allowed = 2
        board.data.votes_allowed = 2

        board.set_visibility(board_module.BOARD_PRIVATE)

        self.assertEqual(board.data.visibility, 0)
        self.assertEqual(board.data.comments_allowed, 1)
        self.assertEqual(board.data.votes_allowed, 1)

    def test_set_visibility_3(self):
        """Test set visibility method 3

        Initial State:
         - board:public
         - allow_comment: members
         - allow_votes: off

        End state
         - board:private
         - allow_comment: members
         - allow_votes: off
        """
        helpers.set_dummy_context()
        board = helpers.create_board()
        board.data.visibility = 1
        board.data.comments_allowed = 1
        board.data.votes_allowed = 0

        board.set_visibility(board_module.BOARD_PRIVATE)

        self.assertEqual(board.data.visibility, 0)
        self.assertEqual(board.data.comments_allowed, 1)
        self.assertEqual(board.data.votes_allowed, 0)

    def test_has_member_1(self):
        """Test has member 1"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user()
        helpers.set_context(user)
        data = board.data  # don't collect
        members = data.members
        members.append(user.data)
        assert(board.has_member(user) is True)

    def test_has_member_2(self):
        """Test has member 2"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        user_2 = helpers.create_user(suffixe='2')
        data = board.data  # don't collect
        data.managers.append(user_2.data)
        assert(board.has_member(user) is False)

    def test_has_manager_1(self):
        """Test has manager 1"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        assert(board.has_manager(user) is False)
        user.data.managed_boards.append(board.data)
        user.data.boards.append(board.data)
        assert(board.has_manager(user) is True)

    def test_has_manager_2(self):
        """Test has manager 2"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        user_2 = helpers.create_user(suffixe='2')
        assert(board.has_manager(user) is False)
        data = board.data  # don't collect
        data.managers.append(user_2.data)
        data.members.append(user_2.data)
        database.session.flush()
        assert(board.has_manager(user) is False)

    def test_add_member_1(self):
        """Test add member"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        assert(board.has_member(user) is False)
        board.add_member(user)
        assert(board.has_member(user) is True)
