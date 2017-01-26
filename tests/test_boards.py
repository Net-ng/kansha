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
from elixir import metadata as __metadata__

from kansha import helpers
from kansha.board import boardsmanager
from kansha.board.models import DataBoard
from kansha.board import comp as board_module


database.set_metadata(__metadata__, 'sqlite:///:memory:', False, {})


# FIXME: dirty tests; rewrite them all on component API.

class BoardTest(unittest.TestCase):

    def setUp(self):
        helpers.setup_db(__metadata__)
        self.boards_manager = helpers.get_boards_manager()

    def tearDown(self):
        helpers.teardown_db(__metadata__)

    def test_add_board(self):
        """Create a new board"""
        helpers.set_dummy_context()
        self.assertEqual(DataBoard.query.count(), 0)
        helpers.create_board()
        self.assertEqual(DataBoard.query.filter_by(is_template=False).count(), 1)

    def test_add_column_ok(self):
        """Add a column to a board"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        self.assertIsNotNone(board.archive_column)
        self.assertEqual(board.count_columns(), 4)
        board.create_column(0, helpers.word())
        self.assertEqual(board.count_columns(), 5)

    def test_add_column_ko(self):
        """Add a column with empty title to a board"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        self.assertEqual(board.count_columns(), 4)
        self.assertFalse(board.create_column(0, ''))

    def test_delete_column(self):
        """Delete column from a board"""
        helpers.set_dummy_context()
        user = helpers.create_user()
        helpers.set_context(user)
        board = helpers.create_board()
        self.assertIsNotNone(board.archive_column)
        self.assertEqual(board.count_columns(), 4)
        column = board.columns[0]
        board.delete_column(column)
        self.assertEqual(board.count_columns(), 3)

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

    def test_save_as_template(self):
        title = helpers.word()
        description = helpers.word()
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user()
        helpers.set_context(user)
        boards_manager = helpers.get_boards_manager()
        template = boards_manager.create_template_from_board(board, title, description, False)
        self.assertEqual(template.data.title, title)
        self.assertEqual(template.data.description, description)
        self.assertTrue(template.data.is_template)
        self.assertEqual(template.data.visibility, board_module.BOARD_PRIVATE)
        template = boards_manager.create_template_from_board(board, title, description, True)
        self.assertEqual(template.data.visibility, board_module.BOARD_PUBLIC)

    def test_switch_view(self):
        board = helpers.create_board()
        self.assertEqual(board.model, 'columns')
        board.switch_view()
        self.assertEqual(board.model, 'calendar')
        board.switch_view()
        self.assertEqual(board.model, 'columns')

    def test_has_member_1(self):
        """Test has member 1"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        board.add_member(user)
        self.assertTrue(board.has_member(user))

    # def test_has_member_2(self):
    #     """Test has member 2"""
    #     helpers.set_dummy_context()
    #     board = helpers.create_board()
    #     user = helpers.create_user('bis')
    #     helpers.set_context(user)
    #     user_2 = helpers.create_user(suffixe='2')
    #     board.add_member(user_2, role='manager')
    #     self.assertFalse(board.has_member(user))

    def test_has_manager_1(self):
        """Test has manager 1"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        self.assertFalse(board.has_manager(user))
        board.add_member(user, role='manager')
        self.assertTrue(board.has_manager(user))

    def test_has_manager_2(self):
        """Test has manager 2"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        user_2 = helpers.create_user(suffixe='2')
        self.assertFalse(board.has_manager(user))
        board.add_member(user_2, role='manager')
        database.session.flush()
        self.assertTrue(board.has_manager(user_2))
        self.assertFalse(board.has_manager(user))

    def test_add_member_1(self):
        """Test add member"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        self.assertFalse(board.has_member(user))
        board.add_member(user)
        self.assertTrue(board.has_member(user))

    def test_change_role(self):
        '''Test change role'''
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('test')
        board.add_member(user)
        board.update_members()

        def find_board_member():
            for member in board.all_members:
                print member().user(), user
                if member().user() == user:
                    return member()

        member = find_board_member()
        self.assertEqual(len(board.members), 1)
        self.assertEqual(len(board.managers), 1)

        member.dispatch('toggle_role', '')
        member = find_board_member()
        board.update_members()
        self.assertEqual(len(board.members), 0)
        self.assertEqual(len(board.managers), 2)

        member.dispatch('toggle_role', '')
        board.update_members()
        self.assertEqual(len(board.members), 1)
        self.assertEqual(len(board.managers), 1)

    def test_get_boards(self):
        '''Test get boards methods'''

        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user()
        user2 = helpers.create_user('bis')
        board.add_member(user2, 'member')
        boards_manager = helpers.get_boards_manager()
        self.assertTrue(board.has_manager(user))
        self.assertFalse(board.has_manager(user2))

        def in_comp(obj, comp_list):
            return any(obj == comp() for comp in comp_list)

        helpers.set_context(user)
        boards_manager.load_user_boards()
        self.assert_(not in_comp(board, boards_manager.last_modified_boards))
        self.assert_(not in_comp(board, boards_manager.guest_boards))
        self.assert_(in_comp(board, boards_manager.my_boards))
        self.assert_(not in_comp(board, boards_manager.archived_boards))

        helpers.set_context(user2)
        boards_manager.load_user_boards()
        self.assert_(not in_comp(board, boards_manager.last_modified_boards))
        self.assert_(in_comp(board, boards_manager.guest_boards))
        self.assert_(not in_comp(board, boards_manager.my_boards))
        self.assert_(not in_comp(board, boards_manager.archived_boards))

        column = board.create_column(1, u'test')
        column.create_card(u'test')
        boards_manager.load_user_boards()
        self.assert_(in_comp(board, boards_manager.last_modified_boards))

        board.archive()
        boards_manager.load_user_boards()
        self.assert_(in_comp(board, boards_manager.archived_boards))

    def test_get_by(self):
        '''Test get_by_uri and get_by_id methods'''
        helpers.set_dummy_context()
        orig_board = helpers.create_board()
        board = self.boards_manager.get_by_id(orig_board.id)
        self.assertEqual(orig_board.data.id, board.data.id)
        self.assertEqual(orig_board.data.title, board.data.title)
        board = self.boards_manager.get_by_uri(orig_board.data.uri)
        self.assertEqual(orig_board.data.id, board.data.id)
        self.assertEqual(orig_board.data.title, board.data.title)
