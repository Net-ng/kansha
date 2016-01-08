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
    def get_all(cls, card):
        return cls.query.filter_by(card=card).all()

    @classmethod
    def add(cls, filename, card, author):
        return cls(filename=filename, card=card, author=author,
                   creation_date=datetime.datetime.utcnow())

    @classmethod
    def remove(cls, card, filename):
        file = cls.get_by_filename(filename)
        file.delete()

    @classmethod
    def remove_all(cls, card):
        cls.query.filter_by(card=card).delete()

    @classmethod
    def has_cover(cls, card):
        q = cls.query
        q = q.filter_by(cover=card)
        return q.count() == 1

    @classmethod
    def get_cover(cls, card):
        q = cls.query
        q = q.filter_by(cover=card)
        return q.first()

    @classmethod
    def set_cover(cls, card, asset):
        asset.cover = card

    @classmethod
    def remove_cover(cls, card):
        asset = cls.get_cover(card)
        asset.cover = None

    @classmethod
    def get_by_filename(cls, filename):
        return cls.get(filename)
