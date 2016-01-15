# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import security

from kansha.cardextension.tests import CardExtensionTestCase

from .comp import Comments


class CommentsTest(CardExtensionTestCase):

    extension_name = 'comments'
    extension_class = Comments

    def test_add_delete(self):
        self.assertEqual(len(self.extension.comments), 0)
        self.extension.add(u'test')
        self.assertEqual(len(self.extension.comments), 1)
        comment = self.extension.comments[0]()
        self.assertEqual(comment.data.comment, u'test')
        comment.set_comment(u'test2')
        self.assertEqual(comment.data.comment, u'test2')
        self.extension.delete_comment(self.extension.comments[0])

    def test_comment_label(self):
        self.extension.add(u'test')
        label = self.extension.comments[0]().comment_label()
        self.assertEqual(label.text, u'test')
        label.change_text(u'test2')
        self.assertEqual(label.text, u'test2')
        self.assertTrue(label.is_author(security.get_user()))

    def test_to_indexable(self):
        self.extension.add(u'Comment 1')
        self.extension.add(u'Comment 2')
        self.extension.add(u'Comment 3')
        self.assertEqual(self.extension.to_indexable(), u'''Comment 3
Comment 2
Comment 1''')

