#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from datetime import date

from peak.rules import when
from nagare.security import common
from nagare.i18n import _, format_date
from nagare import component, security

from kansha.card import Card
from kansha.board import excel_export
from kansha.toolbox import calendar_widget
from kansha.cardextension import CardExtension

from .models import DataCardDueDate


@when(common.Rules.has_permission, "user and perm == 'due_date' and isinstance(subject, Card)")
def has_permission_Card_due_date(self, user, perm, card):
    return security.has_permissions('edit', card)


class DueDate(CardExtension):

    LOAD_PRIORITY = 60

    def __init__(self, card, action_log, configurator):
        """Initialization

        In:
            - ``card`` -- the object card
        """
        super(DueDate, self).__init__(card, action_log, configurator)
        self.due_date = self.get_value()
        self.calendar = None

    def _init_calendar(self):
        if self.calendar is None or self.calendar().is_hidden:
            calendar = calendar_widget.Calendar(self.due_date, allow_none=True)
            self.calendar = component.Component(calendar)

    @property
    def data(self):
        data = DataCardDueDate.get_by_card(self.card.data)
        if data is None:
            data = DataCardDueDate(card=self.card.data)
        return data

    def get_value(self):
        return self.data.due_date

    def set_value(self, value):
        '''Set the value to a new date (or None)'''
        self.data.due_date = value
        self.due_date = value

    def new_card_position(self, value):
        self.set_value(value)

    def get_days_count(self):
        today = date.today()
        diff = today - self.due_date
        return diff.days

    def get_class(self):
        '''Get its css class depending on the amount of time between today and the value'''
        if not self.due_date:
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

    def delete(self):
        self.data.delete()


@excel_export.get_extension_title_for(DueDate)
def get_extension_title_DueDate(card_extension):
    return _(u'Due date')


@excel_export.write_extension_data_for(DueDate)
def write_extension_data_DueDate(self, sheet, row, col, style):
    value = self.get_value()
    sheet.write(row, col, format_date(value) if value else u'', style)
