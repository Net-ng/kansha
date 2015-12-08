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
    creation_date = Field(DateTime)
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
    def create_card(cls, column, title):
        """Create new column

        In:
            - ``column`` -- DataColumn, father of the column
            - ``title`` -- title of the card
        Return:
            - created DataCard instance
        """
        new_card = cls(title=title,
                       creation_date=datetime.datetime.utcnow())
        column.cards.append(new_card)
        return new_card

    @classmethod
    def get_all(cls):
        query = cls.query.options(subqueryload('labels'), subqueryload('comments'))
        return query

    def make_cover(self, asset):
        """
        """
        DataCard.get(self.id).cover = asset.data

    def remove_cover(self):
        """
        """
        DataCard.get(self.id).cover = None

    def remove_board_member(self, member):
        """Remove member from board"""
        if member.get_user_data() in self.members:
            self.members.remove(member.get_user_data())
            session.flush()
