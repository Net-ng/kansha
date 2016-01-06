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

from kansha.models import Entity


class DataComment(Entity):

    """Comment mapper
    """
    using_options(tablename='comment')
    comment = Field(UnicodeText, default=u'')
    creation_date = Field(DateTime)
    card = ManyToOne('DataCard')
    author = ManyToOne('DataUser')
