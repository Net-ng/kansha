# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from __future__ import absolute_import

from datetime import datetime, timedelta
import json
import urlparse

from elixir import using_options
from elixir import ManyToOne
from elixir import Field, Unicode, UnicodeText, DateTime
from nagare import database, log, presentation, var, ajax
from nagare.i18n import _, _L, format_datetime
from nagare.namespaces import xhtml
from sqlalchemy.types import TypeDecorator
import sqlalchemy as sa

from kansha.models import Entity
from kansha.user.models import DataBoardMember


# Levels
NOTIFY_OFF = 0
NOTIFY_MINE = 1
NOTIFY_ALL = 2


# Groups and messages
EVENT_MESSAGES = {
    'card_create': _L(u'Card "%(card)s" has been added to column "%(column)s"'),
    'card_delete': _L(u'User %(author)s has deleted card "%(card)s"'),
    'card_archive': _L(u'User %(author)s has archived card "%(card)s"'),
    'card_move': _L(u'Card "%(card)s" has been moved from column "%(from)s" to column "%(to)s"'),
    'card_title': _L(u'Card "%(from)s" has been renamed to "%(to)s"'),
    'card_weight': _L(u'Card "%(card)s" has been weighted from (%(from)s) to (%(to)s)'),
    'card_add_member': _L(u'User %(user)s has been assigned to card "%(card)s"'),
    'card_remove_member': _L(u'User %(user)s has been unassigned from card "%(card)s"'),
    'card_add_comment': _L(u'User %(author)s has commented card "%(card)s"'),
    'card_add_file': _L(u'User %(author)s has added file "%(file)s" to card "%(card)s"'),
    'card_add_list': _L(u'User %(author)s has added the checklist "%(list)s" to card "%(card)s"'),
    'card_delete_list': _L(u'User %(author)s has deleted the checklist "%(list)s" from card "%(card)s"'),
    'card_listitem_done': _L(u'User %(author)s has checked the item %(item)s from the checklist "%(list)s", on card "%(card)s"'),
    'card_listitem_undone': _L(u'User %(author)s has unchecked the item %(item)s from the checklist "%(list)s", on card "%(card)s"'),
}

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


# Models

class JSONType(TypeDecorator):
    impl = UnicodeText

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = unicode(json.dumps(value))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class DataHistory(Entity):
    using_options(tablename='history', order_by='-when')

    when = Field(DateTime)
    action = Field(Unicode(255))
    data = Field(JSONType)

    board = ManyToOne('DataBoard', ondelete='cascade')
    card = ManyToOne('DataCard', ondelete='cascade')
    user = ManyToOne('DataUser', ondelete='cascade')


def add_history(board, card, user, action, data):
    data.update(action=action)
    when = datetime.utcnow()
    data = DataHistory(
        when=when, action=action, board=board, card=card, user=user, data=data)
    database.session.add(data)
    database.session.flush()


def get_board_member(user, board):
    query = DataBoardMember.query
    query = query.filter_by(member=user.data)
    query = query.filter_by(board=board.data)
    return query.first()


def allow_notifications(user, board, level):
    get_board_member(user, board).notify = level


def notifications_allowed(user, board):
    return get_board_member(user, board).notify


def get_subscribers():
    q = database.session.query(DataBoardMember)
    q = q.filter(sa.or_(DataBoardMember.notify == NOTIFY_ALL,
                        DataBoardMember.notify == NOTIFY_MINE))
    return q


def get_events(board, hours=None):
    '''board to None means "everything".'''
    since = datetime.utcnow() - timedelta(hours=hours)
    q = DataHistory.query
    if board:
        q = q.filter_by(board=board)
    q = q.filter(DataHistory.when >= since)
    q = q.order_by(DataHistory.board_id, DataHistory.action, DataHistory.when)
    return q.all()


def get_history(board, cardid=None, username=None):
    q = DataHistory.query
    q = q.filter_by(board=board)
    if cardid:
        q = q.filter(DataHistory.card.has(id=cardid))
    if username:
        q = q.filter(DataHistory.user.has(username=username))
    return q


def filter_events(events, subscriber):
    if subscriber.notify == NOTIFY_ALL:
        return [event for event in events]
    elif subscriber.notify == NOTIFY_MINE:
        user_cards = set([card.id for card in subscriber.member.cards])
        return [event for event in events if event.card_id in user_cards]
    return []

# component


class ActionLog(object):

    def __init__(self, board):
        self.board = board
        self.user_id = var.Var('')
        self.card_id = var.Var(None)


# renders

def render_event(event):
    data = event.data.copy()
    data['author'] = event.user.fullname or event.user.username
    msg = EVENT_MESSAGES.get(event.action)
    if msg is not None:
        return _(msg) % data
    log.error('Undefined event type "%s"', event.action)
    return u''


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
                            event = h.a(render_event(event), href='%s#id_card_%s' % (
                                data['url'], event.card.id), style='text-decoration: none;')
                        else:
                            event = render_event(event)
                        root.append(h.li(event))

            ret.append(_(GROUP_MESSAGES[group]))
            ret.append('')
            for event in events:
                ret.append(u'- ' + render_event(event))
            ret.append(u'')

    ret.append(
        _(u'To unsubscribe from board "%(board)s" alerts, click on %(url)s and modify notifications parameters in the "settings" menu of the "Board" tab.') % data)
    root.append(h.p(_(u'To unsubscribe from board "%(board)s" alerts, ') % data,
                    h.a(_(u'click here'), href=data['url']),
                    _(' and modify notifications parameters in the "settings" menu of the "Board" tab.') % data, style='border: 1px solid black; padding: 5px; text-align: center;'))

    return subject, u'\n'.join(ret), root.write_htmlstring()


@presentation.render_for(ActionLog)
def render(self, h, *_args):
    return h.root


@presentation.render_for(ActionLog, 'history')
def render_history(self, h, *_args):
    h << h.h2(_('Action log'))
    board = self.board.data
    with h.select(onchange=ajax.Update(action=self.user_id)):
        h << h.option(_('all users'), value='')
        for member in board.members:
            h << h.option(member.fullname, value=member.username).selected(
                self.user_id())
    with h.select(onchange=ajax.Update(action=lambda x: self.card_id(int(x)))):
        h << h.option(_('all cards'), value=0)
        for col in board.columns:
            for card in col.cards:
                h << h.option(card.title, value=card.id).selected(
                    self.card_id())
    with h.div(class_='history row-fluid'):
        with h.table(class_='table table-striped table-hover'):
            with h.body:
                for event in get_history(board, cardid=self.card_id(), username=self.user_id()):
                    with h.tr:
                        h << h.th(format_datetime(event.when, 'short'))
                        h << h.td(render_event(event))
    return h.root
