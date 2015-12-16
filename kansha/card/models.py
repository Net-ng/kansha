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
from elixir import ManyToMany, ManyToOne, OneToMany, OneToOne
from elixir import Field, Unicode, Integer, DateTime, Date, UnicodeText
from sqlalchemy.orm import subqueryload
from nagare.database import session
import datetime

from kansha.models import Entity


class DataCard(Entity):

    """Card mapper
    """
    using_options(tablename='card')
    title = Field(UnicodeText)
    description = Field(UnicodeText, default=u'')
    index = Field(Integer)
    creation_date = Field(DateTime, default=datetime.datetime.utcnow)
    column = ManyToOne('DataColumn')

    # feature data to move to card extensions
    votes = OneToMany('DataVote')
    labels = ManyToMany('DataLabel')
    comments = OneToMany('DataComment', order_by="-creation_date")
    assets = OneToMany('DataAsset', order_by="-creation_date")
    checklists = OneToMany('DataChecklist', order_by="index")
    members = ManyToMany('DataUser')
    cover = OneToOne('DataAsset', inverse="cover")
    due_date = Field(Date)
    weight = Field(Unicode(255), default=u'')

    def copy(self, parent):
        new_data = DataCard(title=self.title,
                            description=self.description,
                            weight=self.weight,
                            column=parent)
        session.flush()
        return new_data

    @classmethod
    def get_all(cls):
        query = cls.query.options(subqueryload('labels'), subqueryload('comments'))
        return query

    # Methods for data belonging to card extensions

    def make_cover(self, asset):
        """
        """
        DataCard.get(self.id).cover = asset.data

    def remove_cover(self):
        """
        """
        DataCard.get(self.id).cover = None

    def remove_member(self, datauser):
        if datauser in self.members:
            self.members.remove(datauser)

    @property
    def archived(self):
        return self.column.archive
