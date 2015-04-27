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
from elixir import Entity, ManyToOne
from elixir import Field, Unicode, DateTime


class DataToken(Entity):
    using_options(tablename='token')
    token = Field(Unicode(255), unique=True, nullable=False, primary_key=True)
    username = Field(Unicode(255), nullable=True)
    date = Field(DateTime, nullable=False)
    action = Field(Unicode(255), nullable=True)
    board = ManyToOne('DataBoard')

    @classmethod
    def delete_token_by_username(cls, username, action):
        token = cls.get_by(username=username, action=action)
        if token:
            token.delete()
