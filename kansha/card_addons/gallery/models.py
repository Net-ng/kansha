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

    def get_data(self):
        return DataAsset.get_data_by_card(self.card)

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
    cover = ManyToOne('DataCard')

    @classmethod
    def get_data_by_card(cls, card):
        q = cls.query
        q = q.filter_by(card=card)
        return q.all()

    @classmethod
    def get_cover_for_card(cls, card):
        q = cls.query
        q = q.filter_by(cover=card)
        return q.first()

    @classmethod
    def has_cover_for_card(cls, card):
        q = cls.query
        q = q.filter_by(cover=card)
        return q.count() == 1

    @classmethod
    def add_asset(cls, filename, card, author):
        return cls(filename=filename, card=card.data, author=author.data,
                   creation_date=datetime.datetime.utcnow())

    @classmethod
    def get_by_filename(cls, filename):
        return cls.get(filename)
