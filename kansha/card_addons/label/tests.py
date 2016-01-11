# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from datetime import date, timedelta

from kansha.cardextension.tests import CardExtensionTestCase

from .comp import CardLabels


class CardLabelsTest(CardExtensionTestCase):
    def create_instance(self, card, action_log):
        return CardLabels(card, action_log)

    def test_activate(self):
        self.assertTrue(self.extension.get_available_labels() > 0)
        self.assertEqual(len(self.extension.labels), 0)
        label_id = self.extension.get_available_labels()[0].id
        self.extension.activate(label_id)
        self.assertIn(label_id, self.extension.labels)
        self.extension.activate(label_id)
        self.assertNotIn(label_id, self.extension.labels)

    def test_copy(self):
        label_ids = [self.extension.get_available_labels()[index].id for index in xrange(2)]
        for label_id in label_ids:
            self.extension.activate(label_id)
        cpy = self.extension.copy(self.card_copy, {'labels': self.extension.get_available_labels()})
        for label_id in label_ids:
            self.assertIn(label_id, cpy.labels)
