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

from .comp import Votes
from .models import DataVote

database.set_metadata(__metadata__, 'sqlite:///:memory:', False, {})


class VoteTest(unittest.TestCase):
    def setUp(self):
        helpers.setup_db(__metadata__)
        helpers.set_context(helpers.create_user())
        board = helpers.create_board()
        column = board.create_column(1, u'test')
        card = column.create_card(u'test')
        self.votes = Votes(card, None)

    def tearDown(self):
        helpers.teardown_db(__metadata__)

    def test_vote_and_unvote(self):
        self.votes.vote()
        self.assertEqual(self.votes.count_votes(), 1)
        self.assertTrue(self.votes.has_voted())
        self.votes.unvote()
        self.assertEqual(self.votes.count_votes(), 0)
        self.assertFalse(self.votes.has_voted())
