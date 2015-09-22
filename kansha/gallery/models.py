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
from elixir import ManyToOne, Field, Unicode, DateTime, using_options
from nagare import security

from kansha.models import Entity


class DataGallery(object):

    def __init__(self, card):
        self.card = card

    def get_assets(self):
        return DataAsset.get_assets(self.card)

    def get_asset(self, filename):
        return DataAsset.get_by_filename(filename)

    def add_asset(self, filename):
        return DataAsset.add_asset(filename, self.card, security.get_user())

    def delete(self, filename):
        DataAsset.get(filename).delete()


class DataAsset(Entity):

    using_options(tablename='asset')
    filename = Field(Unicode(255), primary_key=True)
    creation_date = Field(DateTime)
    author = ManyToOne('DataUser')
    card = ManyToOne('DataCard')
    cover = ManyToOne('DataCard', inverse="cover")

    @classmethod
    def add_asset(cls, filename, card, author):
        return cls(filename=filename, card=card.data, author=author.data,
                   creation_date=datetime.datetime.utcnow())

    @classmethod
    def get_assets(cls, card):
        """Return all assets"""
        q = cls.query
        q = q.filter(cls.card == card.data)
        return q.all()

    @classmethod
    def get_by_filename(cls, filename):
        return cls.get(filename)
        # TODO check permissions
        """if data_asset:
            data_board = data_asset.card.column.board
            if security.has_permissions('view', data_board):
                return data_asset"""
