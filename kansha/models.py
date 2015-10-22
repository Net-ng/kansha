# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from __future__ import absolute_import

from elixir import using_options
from elixir import DateTime
from elixir import EntityBase
from elixir import EntityMeta
from elixir import ManyToOne
from elixir import Field
from elixir import Unicode

from kansha import pickle


class Entity(EntityBase, pickle.UnpicklableMixin):
    __metaclass__ = EntityMeta
