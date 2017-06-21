# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.i18n import _
from nagare import component, editor, i18n, security, var, validator as nagare_validator

from kansha import title
from kansha import events
from kansha import exceptions
from kansha.toolbox import popin, overlay
from kansha.card import Card, NewCard

from .models import DataColumn


class Column(events.EventHandlerMixIn):

    """Column component
    """

    def __init__(self, id_, board, card_extensions, action_log, card_filter,
                 search_engine_service, services_service, data=None):
        """Initialization

        In:
            - ``id_`` -- the id of the column
        """
        self.db_id = id_
        self._data = data
        self.id = 'list_' + str(self.db_id)
        self.board = board
        self._services = services_service
        self.action_log = action_log
        self.card_filter = card_filter
        self.search_engine = search_engine_service
        self.card_extensions = card_extensions
        self.body = component.Component(self, 'body')
        self.title = component.Component(
            title.EditableTitle(self.get_title)).on_answer(self.set_title)
        self.card_counter = component.Component(CardsCounter(self))
        self._cards = None
        self.new_card = component.Component(
            NewCard(self))

    @property
    def cards(self):
        if self._cards is None:
            self._cards = [
                component.Component(
                    self._services(
                        Card, c.id,
                        self.card_extensions,
                        self.action_log,
                        self.card_filter,
                        data=c))
                for c in self.data.cards]
        return self._cards

    def update(self, other):
        self.data.update(other.data)
        cards_to_index = []
        for card_comp in other.cards:
            card = card_comp()
            new_card = self.create_card(card.get_title())
            new_card.update(card)
            cards_to_index.append(new_card)
        self.index_cards(cards_to_index)

    def index_cards(self, cards, update=False):
        for card in cards:
            card.add_to_index(self.search_engine, self.board.id, update=update)
        self.search_engine.commit(True)

    def actions(self, action, comp):
        if action == 'empty':
            self.empty()
        elif action == 'delete':
            self.emit_event(comp, events.ColumnDeleted, comp)
        elif action == 'purge':
            self.purge_cards()
        self.emit_event(comp, events.SearchIndexUpdated)

    def ui_create_card(self, comp, title):
        if not security.has_permissions('edit', self):
            return
        card = self.create_card(title)
        if card:
            self.index_cards([card])
            self.emit_event(comp, events.SearchIndexUpdated)
            self.card_filter.reset()

    def on_event(self, comp, event):
        if event.is_(events.CardClicked):
            card_comp = event.data
            card_comp.becomes(popin.Popin(card_comp, 'edit'))
        elif event.is_(events.ParentTitleNeeded):
            return self.get_title()
        elif event.is_(events.CardEditorClosed):
            card_bo = event.emitter
            slot = event.data
            slot.becomes(card_bo)
            # if card has been edited, reindex
            if security.has_permissions('edit', card_bo):
                card_bo.add_to_index(self.search_engine, self.board.id, update=True)
                self.search_engine.commit(True)
                self.emit_event(comp, events.SearchIndexUpdated)
            card_bo.refresh()
        elif event.is_(events.CardArchived):
            self.remove_card_by_id(event.last_relay.id)

    @property
    def data(self):
        """Return the column object from the database
        """
        if self._data is None:
            self._data = DataColumn.get(self.db_id)
        return self._data

    def __getstate__(self):
        self._data = None
        return self.__dict__

    def set_title(self, title):
        """Set title

        In:
            - ``title`` -- new title
        """
        self.data.title = title

    def get_title(self):
        """Get title

        Return :
            - the board title
        """
        if self.is_archive:
            return i18n._(u'Archived cards')
        return self.data.title

    def delete(self, purge=False):
        """Delete itself"""
        if not self.data:
            return
        if purge:
            self.purge_cards()
        else:
            self.empty()
        DataColumn.delete_column(self.data)

    def empty(self):
        # FIXME: move this function to board only, use Events
        self.board.archive_cards([card() for card in self.cards], self)
        self._cards = None

    def remove_card_comp(self, card):
        self.cards.remove(card)
        business = card()
        if isinstance(business, popin.Popin):
            business = business.get_business_object()
        self.data.remove_card(business.data)

    def remove_card_by_id(self, card_id):
        """Remove card and return corresponding Component."""
        # find component
        card_comp = filter(lambda x: x().id == card_id, self.cards)[0]
        try:
            self.remove_card_comp(card_comp)
        except (IndexError, ValueError):
            raise ValueError(u'Card has been deleted or does not belong to this list anymore')
        return card_comp

    def insert_card(self, index, card):
        inserted = False
        # TODO: when column extensions are introduced, generalize this
        if self.card_counter().check_add(card) and self.data.insert_card(index, card.data):
            self.cards.insert(index, component.Component(card))
            inserted = True
        return inserted

    def insert_card_comp(self, comp, index, card_comp):
        inserted = False
        card = card_comp()
        # TODO: when column extensions are introduced, generalize this
        if self.card_counter().check_add(card) and self.data.insert_card(index, card_comp().data):
            self.cards.insert(index, card_comp)
            card_comp.on_answer(self.handle_event, comp)
            inserted = True
        return inserted

    def delete_card(self, card):
        """Delete card

        In:
            - ``card`` -- card to delete
        """
        self.cards.pop(card.index)
        values = {'column_id': self.id, 'column': self.get_title(), 'card': card.get_title()}
        card.action_log.add_history(
            security.get_user(),
            u'card_delete', values)
        self.search_engine.delete_document(card.schema, card.id)
        self.search_engine.commit()
        card.delete()
        self.data.delete_card(card.data)

    def purge_cards(self):
        for card_comp in self.cards:
            card = card_comp()
            values = {'column_id': self.id, 'column': self.get_title(), 'card': card.get_title()}
            card.action_log.add_history(
                security.get_user(),
                u'card_delete', values)
            card.delete()
            self.search_engine.delete_document(card.schema, card.id)
        del self.cards[:]
        self.search_engine.commit()
        self.data.purge_cards()

    def append_card(self, card):
        # TODO: when column extensions are introduced, generalize this
        if self.card_counter().check_add(card) and self.data.append_card(card.data):
            self.cards.append(component.Component(card))

    def create_card(self, text=''):
        """Create a new card

        In:
            - ``text`` -- the title of the new card
        """
        if text:
            if not self.can_add_cards:
                raise exceptions.KanshaException(_('Limit of cards reached fo this list'))
            new_card = self.data.create_card(text, security.get_user().data)
            card_obj = self._services(Card, new_card.id, self.card_extensions, self.action_log,
                                      self.card_filter)
            self.cards.append(component.Component(card_obj, 'new'))
            values = {'column_id': self.id,
                      'column': self.get_title(),
                      'card': new_card.title}
            card_obj.action_log.add_history(
                security.get_user(),
                u'card_create', values)
            return card_obj

    def change_index(self, new_index):
        """Change index of the column

        In:
            - ``index`` -- new index
        """
        self.data.index = new_index

    def set_nb_cards(self, nb_cards):
        self.data.nb_max_cards = int(nb_cards) if nb_cards else None

    @property
    def can_add_cards(self):
        rval = True
        if self.nb_max_cards is not None:
            rval = self.count_cards < self.nb_max_cards
        return rval

    @property
    def nb_max_cards(self):
        return self.data.nb_max_cards

    @property
    def count_cards(self):
        return self.data.get_cards_count()

    @property
    def is_archive(self):
        return self.data.archive

    @is_archive.setter
    def is_archive(self, value):
        self.data.archive = value


class NewColumnEditor(object):

    """Column creator component
    """

    def __init__(self, columns_count):
        """Initialization

        In:
            - ``board`` -- the board the new column will belong
        """
        self.columns_count = columns_count
        self.index = editor.Property(u'').validate(nagare_validator.to_int)
        self.title = editor.Property(u'')
        self.title.validate(lambda v: nagare_validator.to_string(v.strip()).not_empty(_(u'''Can't be empty''')))
        self.nb_cards = editor.Property(u'').validate(self.validate_nb_cards)

    def is_validated(self):
        return all((
            self.index.error is None,
            self.title.error is None,
            self.nb_cards.error is None
        ))

    def validate_nb_cards(self, value):
        if value:
            return nagare_validator.to_int(value)
        return value

    def commit(self, comp):
        if self.is_validated():
            comp.answer((self.index.value, self.title.value, self.nb_cards.value))

    def cancel(self, comp):
        comp.answer(None)


# TODO: move data from column to CardsCounter model and make it a column extension
class CardsCounter(object):

    def __init__(self, column):
        self.column = column
        self.id = self.column.id + '_counter'
        self.text = str(self.column.nb_max_cards or 0)
        self.error = None
        self.editable_counter = component.Component(self)

    # Public methods

    def check_add(self, card=None):
        return not self.column.nb_max_cards or self.column.count_cards < self.column.nb_max_cards

    # Private methods

    def change_nb_cards(self, text):
        """Change the title of our wrapped object

        In:
            - ``text`` -- the new title
        Return:
            - the new title

        """

        self.text = text
        self.column.set_nb_cards(text)
        return text

    def reset_error(self):
        self.error = None

    def validate(self, text, comp):
        self.reset_error()
        nb = int(text) if text else 0
        count = self.column.count_cards
        if not nb or nb >= count:
            self.change_nb_cards(nb)
            comp.answer()
        else:
            self.error = _('Must be bigger than %s') % count
