#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.services import plugin


class CardExtension(plugin.Plugin):
    CATEGORY = 'card-extension'

    def __init__(self, card):
        self.card = card

    def delete(self):
        pass

    def copy(self, parent, additional_data):
            return self.__class__(parent)

    def new_card_position(self, value):
        pass
