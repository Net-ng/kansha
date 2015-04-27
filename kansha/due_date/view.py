#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import peak
import datetime

from nagare import presentation, security, ajax, i18n
from nagare.i18n import _, format_date

from .comp import DueDate


@peak.rules.when(ajax.py2js, (datetime.date,))
def py2js(value, h):
    """Generic method to transcode a Datetime

    In:
      - ``value`` -- the datetime object
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    dt = i18n.to_timezone(value)
    return 'new Date("%s", "%s", "%s")' % (
        dt.year, dt.month - 1, dt.day)


@peak.rules.when(ajax.py2js, (DueDate,))
def py2js(value, h):
    if value.value:
        return ajax.py2js(value.value, h)
    return None


@presentation.render_for(DueDate)
def render_DueDate(self, h, comp, model):
    return h.root


@presentation.render_for(DueDate, model='badge')
def render_DueDate_badge(self, h, *args):
    """Gallery badge for the card"""
    if self.value:
        h << h.span(h.i(class_='icon-time icon-grey'), ' ', self.get_days_count(), class_='label due-date ' + self.get_class(), data_tooltip=format_date(self.value, 'full'))
    return h.root


@presentation.render_for(DueDate, model='button')
def render_DueDate_button(self, h, comp, *args):
    if security.has_permissions('due_date', self.parent):
        id_ = h.generate_id()
        if self.value:
            classes = ['btn', 'btn-small', 'btn-due-date', self.get_class()]
            with h.a(class_=u' '.join(classes), id_=id_).action(self.calendar().toggle):
                classes = ['due-date', self.get_class()]
                h << h.i(class_='icon-time icon-white duedate-icon')
                h << format_date(self.value, 'short')
        else:
            with h.a(class_='btn btn-small', id_=id_).action(self.calendar().toggle):
                h << h.i(class_='icon-time icon-grey')
                h << _('Due date')
        h << self.calendar.on_answer(self.set_value)
    return h.root
