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

from .comp import Checklists

class ChecklistTest(CardExtensionTestCase):

    extension_name = 'checklists'
    extension_class = Checklists

    def test_add_delete(self):
        self.assertEqual(len(self.extension.checklists), 0)
        self.extension.add_checklist()
        self.assertEqual(len(self.extension.checklists), 1)
        with self.assertRaises(IndexError):
            self.extension.delete_checklist(1)
        self.extension.delete_checklist(0)
        self.assertEqual(len(self.extension.checklists), 0)

    def test_title(self):
        ck = self.extension.add_checklist()
        ck.set_title(u'test')
        self.assertEqual(ck.data.title, u'test')
        self.assertEqual(ck.get_title(), u'test')

    def test_items(self):
        ck = self.extension.add_checklist()
        self.assertEqual(ck.total_items, 0)
        ck.add_item_from_str(u'test')
        self.assertEqual(ck.total_items, 1)
        ck.add_item_from_str(u'test2')
        self.assertEqual(ck.total_items, 2)
        ck.add_item_from_str(u'test3')
        self.assertEqual(ck.total_items, 3)
        ck.delete_index(1)
        self.assertEqual(ck.total_items, 2)
        ck.set_index(1)
        self.assertEqual(ck.data.index, 1)
        self.assertEqual(ck.items[0]().get_title(), u'test')
        self.assertEqual(ck.items[1]().get_title(), u'test3')

    def test_item(self):
        ck = self.extension.add_checklist()
        self.assertEqual(ck.total_items, 0)
        self.assertEqual(ck.total_items_done, 0)
        self.assertEqual(ck.progress, 0)
        ck.add_item_from_str(u'test')
        self.assertEqual(ck.total_items, 1)
        self.assertEqual(ck.total_items_done, 0)
        self.assertEqual(ck.progress, 0)
        item = ck.items[0]()
        self.assertEqual(item.get_title(), u'test')
        item.set_title(u'test2')
        self.assertEqual(item.get_title(), u'test2')
        self.assertFalse(item.done)
        item.set_done()
        self.assertTrue(item.done)
        self.assertEqual(ck.total_items, 1)
        self.assertEqual(ck.total_items_done, 1)
        self.assertEqual(ck.progress, 100)
        ck.add_item_from_str(u'test')
        self.assertEqual(ck.progress, 50)
        item.set_done()
        self.assertFalse(item.done)

    def test_copy(self):
        ck = self.extension.add_checklist()
        ck.set_title(u'test')
        ck.set_index(0)
        ck.add_item_from_str(u'test')
        ck.add_item_from_str(u'test2')
        ck.items[0]().set_title(u'test item')
        item = ck.items[1]()
        item.set_title(u'test item2')
        item.set_done()
        ck = self.extension.add_checklist()
        ck.set_title(u'test2')
        ck.set_index(1)
        ck.add_item_from_str(u'test3')

        cpy = self.extension_copy
        self.assertEqual(len(cpy.checklists), 2)
        self.assertEqual(cpy.total_items, 3)
        self.assertEqual(cpy.total_items_done, 0)
        ck = cpy.checklists[0]()
        self.assertEqual(ck.get_title(), u'test')
        self.assertEqual(ck.data.index, 0)
        item = ck.items[0]()
        self.assertEqual(item.get_title(), u'test item')

    def test_update_document(self):
        doc = self.card.schema(docid=None)
        ck = self.extension.add_checklist()
        ck.set_title(u'test list')
        ck.add_item_from_str(u'test item')
        ck.add_item_from_str(u'test item 2')

        ck = self.extension.add_checklist()
        ck.set_title(u'test list 2')
        ck.add_item_from_str(u'test item 3')
        ck.add_item_from_str(u'test item 4')
        self.extension.update_document(doc)
        self.assertEqual(doc.checklists, u'''test list
test item
test item 2
test list 2
test item 3
test item 4''')


