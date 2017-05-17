# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --


# messages

# FIXME: how can extensions use their own .mo files for translations?

from peak.rules import when

from nagare.i18n import _


def render_event(action, data):
    '''Base function to be augmented with peak.rules'''
    return 'Undefined event type "%s"' % action


@when(render_event, "action=='card_create'")
def render_event_card_create(action, data):
    return _(u'User %(author)s has added card "%(card)s" to column "%(column)s"') % data


@when(render_event, "action=='card_delete'")
def render_event_card_delete(action, data):
    return _(u'User %(author)s has deleted card "%(card)s"') % data


@when(render_event, "action=='card_archive'")
def render_event_card_archive(action, data):
    return _(u'User %(author)s has archived card "%(card)s"') % data


@when(render_event, "action=='card_move'")
def render_event_card_move(action, data):
    return _(u'User %(author)s has moved card "%(card)s" from column "%(from)s" to column "%(to)s"') % data


@when(render_event, "action=='card_title'")
def render_event_card_title(action, data):
    return _(u'User %(author)s has renamed card "%(from)s" to "%(to)s"') % data
