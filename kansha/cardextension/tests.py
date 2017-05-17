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
from kansha.services.actionlog import DummyActionLog


class CardExtensionTestCase(unittest.TestCase):

    extension_name = ''
    extension_class = None

    @property
    def card_copy(self):
        new_card = self.column.create_card(self.card.get_title())
        new_card.update(self.card)
        return new_card

    @property
    def extension_copy(self):
        new_card = self.card_copy
        new_extension = dict(new_card.extensions)[self.extension_name]() if self.extension_name else None
        return new_extension

    def setUp(self):
        database.set_metadata(__metadata__, 'sqlite:///:memory:', False, {})
        helpers.setup_db(__metadata__)
        helpers.set_context(helpers.create_user())
        extensions = [(self.extension_name, self.extension_class)] if self.extension_name else []
        self.board = board = helpers.create_board(extensions)
        self.column = column = board.create_column(1, u'test')
        self.card = column.create_card(u'test')
        self.extension = dict(self.card.extensions)[self.extension_name]() if self.extension_name else None

    def tearDown(self):
        helpers.teardown_db(__metadata__)


class DummyParent(object):
    def __init__(self):
        self.action_log = DummyActionLog()
        self.data = None
