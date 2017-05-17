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

from .comp import CardWeightEditor


class CardWeightTest(CardExtensionTestCase):

    extension_name = 'weight'
    extension_class = CardWeightEditor

    def test_copy(self):
        self.extension.weight(u'25')
        self.extension.commit()
        self.assertEqual(self.extension.data.weight, 25)
        cpy = self.extension_copy
        self.assertEqual(self.extension.weight(), cpy.weight())
