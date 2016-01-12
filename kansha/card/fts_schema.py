# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
"""
Model for full text search
"""

from kansha.services.search import schema


class Card(schema.Document):
    title = schema.TEXT(stored=True)
    description = schema.TEXT
    comments = schema.TEXT
    labels = schema.TEXT
    checklists = schema.TEXT
    board_id = schema.INT
    archived = schema.BOOLEAN

    @classmethod
    def from_model(cls, card):
        '''
        Create from card model
        '''
        data = card.to_schema()
        return cls(card.id, **data)
