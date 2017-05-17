# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

#FIXME: this should be a board extension

from __future__ import absolute_import

import urlparse
import sqlalchemy as sa

from nagare import database
from nagare.i18n import _, _L
from nagare.namespaces import xhtml

from kansha.card_addons.members import Membership


# Levels
NOTIFY_OFF = 0
NOTIFY_MINE = 1
NOTIFY_ALL = 2


# Groups
GROUP_EVENTS = (
    ('affected', ('card_add_member', 'card_remove_member')),
    ('modified', ('card_move', 'card_title', 'card_add_file', 'card_add_comment', 'card_weight',
                  'card_add_list', 'card_delete_list', 'card_listitem_done', 'card_listitem_undone')),
    ('add_remove', ('card_create', 'card_delete', 'card_archive'))
)

GROUP_MESSAGES = {
    'affected': _L(u'Cards affectation:'),
    'modified': _L(u'Cards modification:'),
    'add_remove': _L(u'Cards addition / removal:')
}


def allow_notifications(user, board, level):
    member = Membership.search(board, user)
    if member:
        member.notify = level


def notifications_allowed(user, board):
    member = Membership.search(board, user)
    return member.notify if member else NOTIFY_OFF


def get_subscribers():
    return Membership.subscribers()


# FIXME: subscriber should be a business object, not a data
def filter_events(events, subscriber):
    if subscriber.notify == NOTIFY_ALL:
        return events
    elif subscriber.notify == NOTIFY_MINE:
        user_cards = set([card.id for card in subscriber.cards])
        return [event for event in events if event.card_id in user_cards]
    return []


# renders

# FIXME: use business objects, not raw data
def generate_email(app_title, board, user, hours, url, events):
    ret = []
    data = {'board': board.title, 'hours': hours, 'url': urlparse.urljoin(
        url, board.url), 'count': len(events), 'app': app_title}
    subject = _(
        u'[%(app)s] Board "%(board)s" - %(count)s new action(s)') % data

    h = xhtml.Renderer()
    root = h.div

    ret.append(
        _(u'The following actions have been made on the board "%(board)s" in the last %(hours)s hours:\n') % data)
    root.append(h.p(_(u'The following actions have been made on the board '),
                    h.a(data['board'], href=data['url']),
                    _(u' in the last %(hours)s hours:') % data))

    groups = {}
    for group, evts in GROUP_EVENTS:
        for event in evts:
            groups[event] = group

    events_by_group = {}
    for e in events:
        events_by_group.setdefault(groups[e.action], []).append(e)

    for group, events in GROUP_EVENTS:
        events = events_by_group.get(group)
        if events:
            with h.div:
                root.append(h.p(
                    _(GROUP_MESSAGES[group]), style='text-decoration: underline; font-weight: bold;'))
                with h.ul:
                    for event in events:
                        if event.card:
                            # IDs are interpreted as anchors since HTML4. So don't use the ID of
                            # the card as a URL fragment, because the browser
                            # jumps to it.
                            event = h.a(event.to_string(), href='%s#id_card_%s' % (
                                data['url'], event.card.id), style='text-decoration: none;')
                        else:
                            event = event.to_string()
                        root.append(h.li(event))

            ret.append(_(GROUP_MESSAGES[group]))
            ret.append('')
            for event in events:
                ret.append(u'- ' + event.to_string())
            ret.append(u'')

    ret.append(
        _(u'To unsubscribe from board "%(board)s" alerts, click on %(url)s and modify notifications parameters in the "settings" menu of the "Board" tab.') % data)
    root.append(h.p(_(u'To unsubscribe from board "%(board)s" alerts, ') % data,
                    h.a(_(u'click here'), href=data['url']),
                    _(' and modify notifications parameters in the "settings" menu of the "Board" tab.') % data, style='border: 1px solid black; padding: 5px; text-align: center;'))

    return subject, u'\n'.join(ret), root.write_htmlstring()
