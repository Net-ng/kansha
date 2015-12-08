# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from datetime import datetime, timedelta
import json

from sqlalchemy.types import TypeDecorator

from elixir import ManyToOne
from elixir import using_options
from elixir import Field, Unicode, UnicodeText, DateTime

from nagare import database
from nagare.i18n import _L, _

from kansha.models import Entity

# messages

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

    def to_string(self):
        data = self.data.copy()
        data['author'] = self.user.fullname or self.user.username
        msg = EVENT_MESSAGES.get(self.action)
        msg = _(msg) % data if msg is not None else 'Undefined event type "%s"', self.action
        return msg

    @classmethod
    def add_history(cls, board, card, user, action, data):
        data.update(action=action)
        when = datetime.utcnow()
        data = cls(
            when=when, action=action, board=board, card=card, user=user, data=data)
        database.session.flush()

    @classmethod
    def get_events(cls, board, hours=None):
        '''board to None means "everything".'''
        since = datetime.utcnow() - timedelta(hours=hours)
        q = cls.query
        if board:
            q = q.filter_by(board=board)
        q = q.filter(cls.when >= since)
        q = q.order_by(cls.board_id, cls.action, cls.when)
        return q.all()

    @classmethod
    def get_history(cls, board, cardid=None, username=None):
        q = cls.query
        q = q.filter_by(board=board)
        if cardid:
            q = q.filter(cls.card.has(id=cardid))
        if username:
            q = q.filter(cls.user.has(username=username))
        return q
