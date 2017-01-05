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
    def get_excel_title():
        '''If the extension is exportable in Excel, return its column name'''
        return None

    @staticmethod
    def get_schema_def():
        '''If the extension has to be indexed for it to be used in search engine, return some schema field
        ie: return schema.Text for a text field'''
        return None

    def update_document(self, document):
        '''Add extension value to document that will be indexed'''
        pass

    def delete(self):
        '''Happens when a card is deleted, use it to clean up files for example'''
        pass

    def update(self, other):
        '''Copy state and data from other on self.'''
        pass

    def new_card_position(self, value):
        '''Happens when a card is moved on the board'''
        pass

    def has_permission_on_card(self, user, perm):
        return True
