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
from kansha.cardextension import CardExtension
from kansha.services.actionlog import DummyActionLog


class CardExtensionTestCase(unittest.TestCase):
    def create_instance(self, card, action_log, configurator):
        return CardExtension(card, action_log, configurator)

    @property
    def card_copy(self):
        return self.card.copy(self.column, {})

    def setUp(self):
        database.set_metadata(__metadata__, 'sqlite:///:memory:', False, {})
        helpers.setup_db(__metadata__)
        helpers.set_context(helpers.create_user())
        self.board = board = helpers.create_board()
        self.column = column = board.create_column(1, u'test')
        self.card = column.create_card(u'test')
        self.extension = self.create_instance(self.card, DummyActionLog(), board)

    def tearDown(self):
        helpers.teardown_db(__metadata__)


class DummyParent(object):
    def __init__(self):
        self.action_log = DummyActionLog()
        self.data = None
