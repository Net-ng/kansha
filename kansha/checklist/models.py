# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from elixir import using_options, Field, OneToMany, ManyToOne, Integer, Unicode, Boolean

from kansha.models import Entity


class DataChecklist(Entity):
    using_options(tablename='checklists')

    title = Field(Unicode(255))
    items = OneToMany('DataChecklistItem', order_by='index', inverse='checklist')
    card = ManyToOne('DataCard')
    author = ManyToOne('DataUser')
    index = Field(Integer)

    def __unicode__(self):
        titles = [item.title for item in self.items if item.title]
        if self.title:
            titles.insert(0, self.title)
        return u'\n'.join(titles)


class DataChecklistItem(Entity):
    using_options(tablename='checklist_items')

    index = Field(Integer)
    title = Field(Unicode(255))
    done = Field(Boolean)
    checklist = ManyToOne('DataChecklist')
