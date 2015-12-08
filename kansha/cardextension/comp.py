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

    def __init__(self, card, action_log):
        self.card = card
        self.action_log = action_log

    def delete(self):
        pass

    def copy(self, parent, additional_data):
            return self.__class__(parent, parent.action_log)

    def new_card_position(self, value):
        pass
