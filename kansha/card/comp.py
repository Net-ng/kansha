# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import dateutil.parser

from nagare import component, security

from kansha import title
from kansha import events
from kansha.services.search import schema
from kansha.services.actionlog.messages import render_event

from .models import DataCard


class NewCard(object):

    """New card component
    """

    def __init__(self, column):
        self.column = column
        self.needs_refresh = False

    def toggle_refresh(self):
        self.needs_refresh = not self.needs_refresh


class Card(events.EventHandlerMixIn):

    """Card component
    """
    schema = schema.Schema('Card',
                           schema.Text(u'title', stored=True),
                           schema.Int('board_id'),
                           schema.Boolean('archived'))

    def __init__(self, id_, card_extensions, action_log, card_filter,
                 services_service, data=None):
        """Initialization

        In:
            - ``id_`` -- the id of the card in the database
            - ``column`` -- father
        """
        self.db_id = id_
        self.id = 'card_' + str(self.db_id)
        self.card_extensions = card_extensions
        self.action_log = action_log.for_card(self)
        self.card_filter = card_filter
        self._services = services_service
        self._data = data
        self.extensions = ()
        self.refresh()

    def add_to_index(self, search_engine, board_id, update=False):
        data = {'docid': self.id,
                'title': self.get_title(),
                'board_id': board_id,
                'archived': self.archived}
        document = self.schema(**data)
        for name, extension in self.extensions:
            extension().update_document(document)
        if update:
            search_engine.update_document(document)
        else:
            search_engine.add_document(document)
        # Don't forget to commit after

    @classmethod
    def update_schema(cls, card_extensions):
        for name, extension in card_extensions.iteritems():
            field = extension.get_schema_def()
            if field is not None:
                cls.schema.add_field(field)

    def update(self, other):
        self.data.update(other.data)
        # extensions must align
        extensions = zip(self.extensions, other.extensions)
        for (name, my_extension), (name2, other_extension) in extensions:
            assert(name == name2)  # should never raise
            my_extension().update(other_extension())

    def refresh(self):
        """Refresh the sub components
        """
        self.title = component.Component(
            title.EditableTitle(self.get_title)).on_answer(self.set_title)
        self.extensions = [
            (name, component.Component(extension))
            for name, extension in self.card_extensions.instantiate_items(self, self.action_log, self._services)
        ]

    @property
    def data(self):
        """Return the card object from the database
        PRIVATE
        """
        if self._data is None:
            self._data = DataCard.get(self.db_id)
        return self._data

    def __getstate__(self):
        self._data = None
        return self.__dict__

    @property
    def archived(self):
        return self.data.archived

    @property
    def index(self):
        return self.data.index

    def can_edit(self, user):
        """
        Has the user the permission to edit this card?
        """
        # if self.extensions is empty, ``all`` returns True, which is what we expect.
        return all(extension().has_permission_on_card(user, 'edit') for __, extension in self.extensions)

    def set_title(self, title):
        """Set title

        In:
            - ``title`` -- new title
        """
        values = {'from': self.data.title, 'to': title}
        self.action_log.add_history(security.get_user(), u'card_title', values)
        self.data.title = title

    def get_title(self):
        """Get title

        Return :
            - the card title
        """
        return self.data.title

    def delete(self):
        """Prepare for deletion"""
        for __, extension in self.extensions:
            extension().delete()
        self.action_log.delete_card()

    def card_dropped(self, request, response):
        """
        Dropped on new date (calendar view).
        """
        start = dateutil.parser.parse(request.GET['start']).date()
        for __, extension in self.extensions:
            extension().new_card_position(start)

    def emit_event(self, comp, kind, data=None):
        if kind == events.PopinClosed:
            kind = events.CardEditorClosed
        return super(Card, self).emit_event(comp, kind, data)
