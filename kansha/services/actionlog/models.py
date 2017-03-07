# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import json
from datetime import datetime, timedelta

from sqlalchemy.types import TypeDecorator

from elixir import ManyToOne
from elixir import using_options
from elixir import Field, Unicode, UnicodeText, DateTime

from nagare import database

from kansha.models import Entity

from .messages import render_event


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
    card = ManyToOne('DataCard', ondelete='cascade', required=True)
    user = ManyToOne('DataUser', ondelete='cascade', required=True)

    def to_string(self):
        data = self.data.copy()
        data['author'] = self.user.fullname or self.user.username
        return render_event(self.action, data)

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

    @classmethod
    def get_last_activity(cls, board):
        q = database.session.query(cls.when)
        q = q.filter(cls.board == board)
        q = q.order_by(cls.when.desc())
        q = q.limit(1)
        return q.scalar()

    @classmethod
    def purge(cls, card):
        q = database.session.query(cls).filter(cls.card == card)
        for log in q:
            log.delete()
