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

    def __init__(self, id_, column, card_extensions, action_log, services_service, data=None):
        """Initialization

        In:
            - ``id_`` -- the id of the card in the database
            - ``column`` -- father
        """
        self.db_id = id_
        self.id = 'card_' + str(self.db_id)
        self.column = column # still used by extensions, not by the card itself
        self.card_extensions = card_extensions
        self.action_log = action_log.for_card(self)
        self._services = services_service
        self._data = data
        self.extensions = ()
        self.refresh()

    @classmethod
    def update_schema(cls, card_extensions):
        for name, extension in card_extensions.iteritems():
            field = extension.get_schema_def()
            if field is not None:
                cls.schema.add_field(field)

    def to_document(self):
        data = {'docid': self.id,
                'title': self.get_title(),
                'board_id': self.column.data.board.id,
                'archived': self.column.is_archive}
        data.update({name: extension().to_indexable() for name, extension in self.extensions})
        return self.schema(**data)

    def copy(self, parent, additional_data):
        new_data = self.data.copy(parent.data)
        new_card = self._services(Card, new_data.id, parent, parent.card_extensions, parent.action_log, data=new_data)
        new_card.extensions = [(name, component.Component(extension().copy(new_card, additional_data)))
                               for name, extension in self.extensions]
        return new_card

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

    ################################
    # Feature methods, persistency #
    ################################

    # Members

    def add_member(self, new_data_member):
        self.data.members.append(new_data_member)

    def remove_member(self, data_member):
        self.data.remove_member(data_member)

    @property
    def members(self):
        return self.data.members

    def remove_board_member(self, member):
        """Member removed from board

        If member is linked to a card, remove it
        from the list of members

        In:
            - ``member`` -- Board Member instance to remove
        """
        self.data.remove_member(member.get_user_data())
        self.refresh()  # brute force solution until we have proper communication between extensions
