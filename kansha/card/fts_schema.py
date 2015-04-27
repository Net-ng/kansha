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
    tags = schema.TEXT
    lists = schema.TEXT
    board_id = schema.INT

    @classmethod
    def from_model(cls, card):
        '''
        Create from card model
        '''
        return cls('card_%d' % card.id,
                   title=card.title,
                   description=card.description,
                   comments='\n'.join(c.comment for c in card.comments),
                   lists='\n'.join(unicode(cl) for cl in card.checklists),
                   tags=' '.join(t.title for t in card.labels),
                   board_id=card.column.board.id)
