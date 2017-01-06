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
from elixir import ManyToMany, ManyToOne
from elixir import Field, Integer, DateTime, UnicodeText
from nagare.database import session
import datetime

from kansha.models import Entity


class DataCard(Entity):
    '''Card mapper'''

    using_options(tablename='card')
    title = Field(UnicodeText)
    index = Field(Integer)
    creation_date = Field(DateTime, default=datetime.datetime.utcnow)
    column = ManyToOne('DataColumn')

    # feature data to move to card extensions
    members = ManyToMany('DataUser', lazy='subquery')

    def update(self, other):
        self.title = other.title
        self.index = other.index
        session.flush()

    # Methods for data belonging to card extensions

    def remove_member(self, datauser):
        if datauser in self.members:
            self.members.remove(datauser)

    @property
    def archived(self):
        return self.column.archive
