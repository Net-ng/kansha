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
from elixir import ManyToOne, ManyToMany
from elixir import Field, Unicode, Integer
from nagare.database import session

from kansha.models import Entity


class DataLabel(Entity):

    """Label mapper
    """
    using_options(tablename='label')
    title = Field(Unicode(255))
    color = Field(Unicode(255))
    board = ManyToOne('DataBoard')
    cards = ManyToMany('DataCard')
    index = Field(Integer)

    def copy(self, parent):
        new_data = DataLabel(title=self.title,
                             color=self.color,
                             index=self.index,
                             board=parent)
        session.add(new_data)
        session.flush()
        return new_data
