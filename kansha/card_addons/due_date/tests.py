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

from .comp import DueDate

class CardDueDateTest(CardExtensionTestCase):

    extension_name = 'due_date'
    extension_class = DueDate

    def test_due_date(self):
        today = date.today()
        self.assertIsNone(self.extension.due_date)
        self.assertIsNone(self.extension.get_value())
        self.extension.set_value(today)
        self.assertEqual(self.extension.get_value(), today)

    def test_days_count(self):
        today = date.today()
        self.extension.set_value(today)
        self.assertEqual(self.extension.get_days_count(), 0)
        self.extension.set_value(today + timedelta(days=5))
        self.assertEqual(self.extension.get_days_count(), -5)
        self.extension.set_value(today - timedelta(days=5))
        self.assertEqual(self.extension.get_days_count(), 5)

    def test_class(self):
        today = date.today()
        self.extension.set_value(today)
        self.assertEqual(self.extension.get_class(), 'today')
        self.extension.set_value(today + timedelta(days=1))
        self.assertEqual(self.extension.get_class(), 'tomorrow')
        self.extension.set_value(today + timedelta(days=10))
        self.assertEqual(self.extension.get_class(), 'future')
        self.extension.set_value(today - timedelta(days=1))
        self.assertEqual(self.extension.get_class(), 'yesterday')
        self.extension.set_value(today - timedelta(days=10))
        self.assertEqual(self.extension.get_class(), 'past')
