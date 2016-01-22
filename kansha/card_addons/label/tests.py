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

from .comp import CardLabels


class CardLabelsTest(CardExtensionTestCase):

    extension_name = 'labels'
    extension_class = CardLabels

    def test_activate(self):
        self.assertTrue(self.extension.get_available_labels() > 0)
        self.assertEqual(len(self.extension.labels), 0)
        label = self.extension.get_available_labels()[0]
        self.extension.activate(label)
        self.assertIn(label, self.extension.labels)
        self.extension.activate(label)
        self.assertNotIn(label, self.extension.labels)

    def test_copy(self):
        labels = self.extension.get_available_labels()
        for label in labels:
            self.extension.activate(label)
        cpy = self.extension_copy
        labels2 = zip(self.extension.labels, cpy.labels)
        for labela, labelb in labels2:
            assert(labela.get_title() == labelb.get_title())

    def test_update_document(self):
        doc = self.card.schema(docid=None)
        label = self.extension.get_available_labels()[0]
        self.extension.activate(label)
        label = self.extension.get_available_labels()[1]
        self.extension.activate(label)
        self.extension.update_document(doc)
        self.assertEqual(doc.labels, u'Green Red')
