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

from elixir import EntityBase
from elixir import EntityMeta

from kansha import pickle


class Entity(EntityBase, pickle.UnpicklableMixin):
    __metaclass__ = EntityMeta

    @classmethod
    def exists(cls, **kw):
        return cls.query.filter_by(**kw).count() > 0
