# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.services import plugins


class CardExtensions(plugins.Plugins):
    ENTRY_POINTS = 'kansha.card.extensions'
    CONFIG_SECTION = 'card_extensions'
