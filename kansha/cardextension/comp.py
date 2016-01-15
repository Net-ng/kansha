#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.services import plugin

from kansha.events import EventHandlerMixIn


class CardExtension(plugin.Plugin, EventHandlerMixIn):
    CATEGORY = 'card-extension'

    def __init__(self, card, action_log, configurator=None):
        self.card = card
        self.action_log = action_log
        self.configurator = configurator

    @staticmethod
    def get_schema_def():
        '''If the extension has to be indexed for it to be used in search engine, return some schema field
        ie: return schema.Text for a text field'''
        return None

    def to_indexable(self):
        '''How to transform extension value for it to be indexed'''
        return None

    def delete(self):
        '''Happens when a card is deleted, use it to clean up files for example'''
        pass

    def copy(self, parent, additional_data):
        '''Happens when a card is copied'''
        configurators = parent.card_extensions.CONFIGURATORS
        return self.__class__(parent, parent.action_log, configurators.get(self.entry_name))

    def new_card_position(self, value):
        '''Happens when a card is moved on the board'''
        pass
