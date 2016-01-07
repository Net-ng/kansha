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
from kansha.cardextension import CardExtension

from .models import DataCardDueDate


class DueDate(CardExtension):

    LOAD_PRIORITY = 60

    def __init__(self, card, action_log):
        """Initialization

        In:
            - ``card`` -- the object card
        """
        super(DueDate, self).__init__(card, action_log)
        self.value = self.get_value()
        self.calendar = calendar_widget.Calendar(self.value, allow_none=True)
        self.calendar = component.Component(self.calendar)

    def get_data(self):
        data = DataCardDueDate.get_data_by_card(self.card.data)
        if data is None:
            data = DataCardDueDate(card=self.card.data)
        return data

    def get_value(self):
        return self.get_data().due_date

    def set_value(self, value):
        '''Set the value to a new date (or None)'''
        data = self.get_data()
        data.due_date = value
        self.value = value

    def new_card_position(self, value):
        self.set_value(value)

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
