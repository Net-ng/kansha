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

from nagare.database import session

from sqlalchemy import func
from elixir import ManyToOne, Field, Unicode, DateTime, using_options

from kansha.models import Entity


class DataAsset(Entity):

    using_options(tablename='asset')
    filename = Field(Unicode(255), primary_key=True)
    creation_date = Field(DateTime)
    author = ManyToOne('DataUser')
    card = ManyToOne('DataCard')
    cover = ManyToOne('DataCard')

    @classmethod
    def get_all(cls, card):
        return cls.query.filter_by(card=card)

    @classmethod
    def count_for(cls, card):
        return cls.get_all(card).with_entities(func.count()).scalar()

    @classmethod
    def add(cls, filename, card, author):
        asset = cls(filename=filename, card=card, author=author,
                   creation_date=datetime.datetime.utcnow())
        session.add(asset)
        session.flush()
        return asset

    @classmethod
    def remove(cls, card, filename):
        file = cls.get_by_filename(filename)
        file.delete()

    @classmethod
    def remove_all(cls, card):
        q = cls.query
        q = q.filter_by(card=card)
        q.delete()

    @classmethod
    def get_cover(cls, card):
        q = cls.query
        q = q.filter_by(cover=card)
        return q.first()

    @classmethod
    def set_cover(cls, card, asset):
        cls.remove_cover(card)
        asset.cover = card

    @classmethod
    def remove_cover(cls, card):
        asset = cls.get_cover(card)
        if asset is not None:
            asset.cover = None

    @classmethod
    def get_by_filename(cls, filename):
        return cls.get(filename)
