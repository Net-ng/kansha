# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
from nagare import presentation
from nagare.services import plugin, plugins

class CardExtension(plugin.Plugin):
    CATEGORY = 'card-extension'

    def __init__(self, card):
        self.card = card

    def copy(self, parent, additional_data):
        return self.__class__(parent)

    def delete(self):
        pass

    def new_card_position(self, value):
        pass


class CardExtensions(plugins.Plugins):
    ENTRY_POINTS = 'kansha.card.extensions'
    CONFIG_SECTION = 'card_extensions'


@presentation.render_for(CardExtension)
@presentation.render_for(CardExtension, 'cover')
@presentation.render_for(CardExtension, 'badge')
@presentation.render_for(CardExtension, 'header')
@presentation.render_for(CardExtension, 'action')
def render(*args):
    return ''
