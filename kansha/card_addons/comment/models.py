# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from elixir import using_options
from elixir import ManyToOne
from elixir import Field, UnicodeText, DateTime
from sqlalchemy import func

from kansha.models import Entity


class DataComment(Entity):

    """Comment mapper
    """
    using_options(tablename='comment')
    comment = Field(UnicodeText, default=u'')
    creation_date = Field(DateTime)
    card = ManyToOne('DataCard')
    author = ManyToOne('DataUser')

    @classmethod
    def get_by_card(cls, card):
        q = cls.query
        q = q.filter_by(card=card)
        q = q.order_by(cls.creation_date.desc())
        return q

    @classmethod
    def total_comments(cls, card):
        q = cls.query
        q = q.filter_by(card=card)
        # query.count() is sloooow, so we use an alternate method
        return q.with_entities(func.count()).scalar()
