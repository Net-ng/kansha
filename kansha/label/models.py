# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import datetime

from elixir import using_options
from elixir import Entity, ManyToOne, ManyToMany
from elixir import Field, Unicode, Integer


class DataLabel(Entity):

    """Label mapper
    """
    using_options(tablename='label')
    title = Field(Unicode(255))
    color = Field(Unicode(255))
    board = ManyToOne('DataBoard')
    cards = ManyToMany('DataCard')
    index = Field(Integer)
