#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from datetime import date

from nagare import component

from kansha.toolbox import calendar_widget


class DueDate(object):

    def __init__(self, parent):
        """Initialization

        In:
            - ``parent`` -- the object parent
        """
        self.parent = parent
        self.value = parent.data.due_date
        self.calendar = calendar_widget.Calendar(self.value, allow_none=True)
        self.calendar = component.Component(self.calendar)

    def set_value(self, value):
        '''Set the value to a new date (or None)'''
        self.parent.data.due_date = value
        self.value = value

    def get_days_count(self):
        today = date.today()
        diff = today - self.value
        return diff.days

    def get_class(self):
        '''Get its css class depending on the amount of time between today and the value'''
        if not self.value:
            return ''
        diff = self.get_days_count()
        if diff < -1:
            return 'future'
        if diff == -1:
            return 'tomorrow'
        if diff == 0:  # Due date is today
            return 'today'
        if diff == 1:
            return 'yesterday'
        if diff > 1:
            return 'past'
        return ''
