#--
# Copyright (c) 2012-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.services import plugin

from kansha.events import EventHandlerMixIn


class ColumnExtension(plugin.Plugin, EventHandlerMixIn):
    CATEGORY = 'column-extension'

    def __init__(self, column, action_log, configurator=None):
        self.column = column
        self.action_log = action_log
        self.configurator = configurator

    def delete(self):
        """Happens when a column is deleted, use it to clean up files for example"""
        pass

    def update(self, other):
        """Copy state and data from other on self."""
        pass

    def new_column_position(self, value):
        """Happens when a column is moved on the board"""
        pass

    def has_permission_on_column(self, user, perm):
        return True
