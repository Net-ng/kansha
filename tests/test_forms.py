# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import logging
import unittest
from . import helpers
from nagare import database
from sqlalchemy import MetaData
from kansha.authentication.database import forms

from elixir import metadata as __metadata__

database.set_metadata(__metadata__, 'sqlite:///:memory:', False, {})


class TokenTest(unittest.TestCase):

    def setUp(self):
        helpers.setup_db(__metadata__)
        self.token_generator = forms.TokenGenerator(u'test_username',
                                                    u'reset_password')

    def tearDown(self):
        helpers.teardown_db(__metadata__)

    def test_create_token(self):
        token = self.token_generator.create_token()

        logging.debug("%s" % token)

        self.assertEqual(token.username, u'test_username')
        self.assertEqual(token.action, u'reset_password')
        self.assertEqual(token.board, None)
