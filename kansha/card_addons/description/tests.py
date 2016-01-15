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

    extension_name = 'description'
    extension_class = CardDescription

    def test_change_desc(self):
        self.extension.text = u'test'
        self.assertEqual(self.extension.text, u'test')
        self.extension.change_text(u'test2')
        self.assertEqual(self.extension.text, u'<p>test2</p>')
        self.assertEqual(self.extension.text, u'<p>test2</p>')

    def test_copy(self):
        self.extension.text = u'test'
        cpy = self.extension_copy
        self.assertEqual(cpy.text, u'test')
