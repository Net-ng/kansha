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
from kansha.services.components_repository import CardExtensions


class Card(schema.Document):
    title = schema.TEXT(stored=True)
    board_id = schema.INT
    archived = schema.BOOLEAN

    @classmethod
    def update_schema(cls, card_extensions):
        for name, extension in card_extensions.items():
            field = extension.get_schema_def()
            if field is not None:
                cls.fields[name] = field
