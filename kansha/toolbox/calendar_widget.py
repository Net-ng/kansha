# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import calendar
from datetime import date, datetime
from dateutil import relativedelta
from nagare import ajax, presentation, i18n, var
from nagare import security
from nagare.i18n import _


YEARS_AROUND = 5


def to_date(v, format='short'):
    '''Format various inputs into a date object
    In:
        - v -- the value to transform
        - format -- if ``v`` is a string, provide the date format used in it
    '''
    if isinstance(v, datetime):
        return v.date()
    elif isinstance(v, (str, unicode)):
        try:
            return i18n.parse_date(v, format)
        except:
            raise ValueError(_('Invalid date format !'))
    return v


def in_(d, start, end):
    '''is ``d`` value between ``start`` and ``end``
    In:
        - d -- a date (or datetime) object'''
    return start <= d <= end


def before(d, start, strict=True):
    '''is ``d`` before ``start``
    In:
        - strict -- ``d`` must be before if True else before or equal
    '''
    if strict:
        return d < start
    return d <= start


def after(d, end, strict=True):
    '''is ``d`` after ``end``
    In:
        - strict -- ``d`` must be after if True else after or equal
    '''
    if strict:
        return d > end
    return d >= end


class Calendar(object):

    def __init__(self, d=None, min_date=None, allow_none=False):
        self.date = d
        self.min_date = min_date
        if self.date is not None:
            val = self.date
        elif self.min_date is not None:
            val = to_date(self.min_date)
        else:
            val = date.today()
        self.current = val.replace(day=1)
        self.is_hidden = True
        self.allow_none = allow_none

    def toggle(self):
        self.is_hidden = not self.is_hidden

    def next_month(self):
        self.current += relativedelta.relativedelta(months=+1)

    def previous_month(self):
        self.current += relativedelta.relativedelta(months=-1)

    def choose_date(self, day, comp):
        self.toggle()
        self.date = self.current.replace(day=day)
        comp.answer(self.date)

    def remove_date(self, comp):
        self.toggle()
        self.date = None
        comp.answer(self.date)

    @property
    def str_date(self):
        if self.date is None:
            return u''
        return i18n.format_date(self.date, 'short')

    def is_authorized_date(self, d):
        if self.min_date is not None and before(d, self.min_date):
            return False
        return True

    def set_today(self):
        self.current = date.today().replace(day=1)

    def change_month(self, month):
        self.current = self.current.replace(month=int(month))

    def change_year(self, year):
        self.current = self.current.replace(year=int(year))

    def __call__(self, value=None):
        if value is not None:
            self.date = to_date(value)
        return self.date


@presentation.render_for(Calendar)
def render_async(self, h, comp, *args):
    display_week_numbers = security.get_user().display_week_numbers
    with h.div(class_='calendar-input'):
        input_id = h.generate_id('input')
        calendar_id = h.generate_id('calendar')
        if self.is_hidden:
            style = 'display: none;'
        else:
            style = 'display: block;'
        with h.div(class_='calendar', id_=calendar_id, style=style):
            with h.div(class_='calendar-header'):
                with h.a(title=_(u'Previous')).action(self.previous_month):
                    h << h.i(class_='icon-arrow-left icon-grey', title=_(u'Previous'))
                with h.span(class_='current'):
                    with h.select(onchange=ajax.Update(action=self.change_month)):
                        for n, month in i18n.get_month_names().iteritems():
                            month = month.capitalize()
                            h << h.option(month, value=n).selected(self.current.month)
                    h << u' '
                    with h.select(onchange=ajax.Update(action=self.change_year)):
                        for year in xrange(self.current.year - YEARS_AROUND, self.current.year + YEARS_AROUND):
                            h << h.option(year, value=year).selected(self.current.year)

                with h.a(title=_(u'Next')).action(self.next_month):
                    h << h.i(class_='icon-arrow-right icon-grey', title=_(u'Next'))

            with h.div(class_='calendar-content'):
                if isinstance(self.date, date):
                    if self.current.year == self.date.year and self.current.month == self.date.month:
                        active = self.date.day
                    else:
                        active = -1
                else:
                    active = -1
                today = date.today()
                if today.month == self.current.month and today.year == self.current.year:
                    today = today.day
                else:
                    today = -1

                with h.table:
                    with h.thead:
                        with h.tr:
                            if display_week_numbers:
                                h << h.th(h.span(_('Wk'), title=_('Week number')), class_='week_number')

                            days = [day.capitalize() for day in i18n.get_day_names().itervalues()]
                            h << [h.th(h.span(d[:2], title=d)) for d in days]
                    with h.tbody:
                        for line in calendar.monthcalendar(self.current.year, self.current.month):
                            with h.tr:
                                if display_week_numbers:
                                    week_number = date(self.current.year, self.current.month, max(1, line[0])).isocalendar()[1]
                                    h << h.td(week_number, class_='week_number')

                                for day in line:
                                    if day == 0:
                                        h << h.td(class_='not-this-month')
                                    else:
                                        authorized = self.is_authorized_date(self.current.replace(day=day))
                                        cls = []
                                        if day == active:
                                            cls.append(u'active')
                                        if day == today:
                                            cls.append(u'today')
                                        if not authorized:
                                            cls.append(u'excluded')
                                        with h.td(class_=' '.join(cls)):
                                            if authorized:
                                                h << h.a(day).action(lambda day=day: self.choose_date(day, comp))
                                            else:
                                                h << h.span(day)
            with h.div(class_='calendar-today'):
                h << h.a(h.i(class_='icon-calendar icon-grey'), _(u"Today"), class_='today-link btn').action(self.set_today)
                if self.allow_none:
                    h << h.a(h.i(class_='icon-remove icon-grey'), _(u'None'), class_='erase btn').action(lambda: self.remove_date(comp))

            h << h.script('''YAHOO.util.Event.onDOMReady(function() {
    var region = YAHOO.util.Dom.getRegion('%(input_id)s');
    YAHOO.util.Dom.setXY('%(calendar_id)s', [region.left, region.bottom + 3]);
    });''' % dict(input_id=input_id, calendar_id=calendar_id), type='text/javascript')

            h << h.div(class_='clear')
    return h.root
