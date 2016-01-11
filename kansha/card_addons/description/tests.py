# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from kansha.cardextension.tests import CardExtensionTestCase

from .comp import CardDescription


class CardDescriptionTest(CardExtensionTestCase):
    def create_instance(self, card, action_log):
        return CardDescription(card, action_log)

    def test_change_desc(self):
        self.extension.set_description(u'test')
        self.assertEqual(self.extension.get_description(), u'test')
        self.extension.change_text(u'test2')
        self.assertEqual(self.extension.get_description(), u'<p>test2</p>')
        self.assertEqual(self.extension.text, u'<p>test2</p>')

    def test_copy(self):
        self.extension.set_description(u'test')
        cpy = self.extension.copy(self.card_copy, {})
        self.assertEqual(cpy.get_description(), u'test')