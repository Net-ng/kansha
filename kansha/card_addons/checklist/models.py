# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from elixir import Boolean
from elixir import Field
from elixir import Integer
from elixir import ManyToOne
from elixir import OneToMany
from elixir import Unicode
from elixir import using_options
from sqlalchemy import func
from sqlalchemy.ext.orderinglist import ordering_list

from nagare import database

from kansha.models import Entity


class DataChecklist(Entity):
    using_options(tablename='checklists')

    title = Field(Unicode(255))
    items = OneToMany('DataChecklistItem', order_by='index', inverse='checklist',
                      collection_class=ordering_list('index'))
    card = ManyToOne('DataCard')
    author = ManyToOne('DataUser')
    index = Field(Integer)

    @classmethod
    def get_by_card(cls, card):
        q = cls.query
        q = q.filter_by(card=card)
        q = q.order_by(cls.index)
        return q.all()

    def update(self, other):
        self.title = other.title
        self.index = other.index
        for item in other.items:
            self.items.append(DataChecklistItem(title=item.title,
                                                index=item.index,
                                                done=False))
        database.session.flush()

    def __unicode__(self):
        titles = [item.title for item in self.items if item.title]
        if self.title:
            titles.insert(0, self.title)
        return u'\n'.join(titles)

    def to_indexable(self):
        return unicode(self)

    def add_item_from_str(self, text):
        item = DataChecklistItem.new_from_str(text)
        return self.add_item(item)

    def add_item(self, item):
        self.items.append(item)
        return item

    def insert_item(self, index, item):
        self.items.insert(index, item)

    def remove_item(self, item):
        self.items.remove(item)

    def delete_item(self, item):
        self.remove_item(item)
        item.delete()

    def purge(self):
        for item in self.items:
            item.delete()

    @staticmethod
    def total_items(card):
        return DataChecklistItem.total_items(card)

    @staticmethod
    def total_items_done(card):
        return DataChecklistItem.total_items_done(card)


class DataChecklistItem(Entity):
    using_options(tablename='checklist_items')

    index = Field(Integer)
    title = Field(Unicode(255))
    done = Field(Boolean)
    checklist = ManyToOne('DataChecklist')

    @classmethod
    def new_from_str(cls, text):
        item = cls(title=text.strip())
        database.session.flush()
        return item

    @classmethod
    def total_items(cls, card):
        # query.count() is sloooow, so we use an alternate method
        q = cls.query.join(DataChecklist).filter(DataChecklist.card == card)
        return q.with_entities(func.count()).scalar()

    @classmethod
    def total_items_done(cls, card):
        # query.count() is sloooow, so we use an alternate method
        q = cls.query.join(DataChecklist).filter(DataChecklist.card == card).filter(
            DataChecklistItem.done == True)
        return q.with_entities(func.count()).scalar()
