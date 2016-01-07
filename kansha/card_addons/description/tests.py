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

from .comp import CardDescription


class CardDescriptionTest(CardExtensionTestCase):
    def create_instance(self, card, action_log):
        return CardDescription(card, action_log)