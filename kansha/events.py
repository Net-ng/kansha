# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --


class EventHandlerMixIn(object):
    """
    Mix-in that implements:
      - `emit_event`, to emit an event;
      - `handle_event`, a callback for comp.on_answer if comp is expected to emit events.

      `handle_event` calls a method `on_event(event)`
      on `self` (if exists) to handle the event and then systematically bubbles the event up.
      `handle_event` returns the return value of `on_event`
      if any, or the return value of the upper levels.
    """

    def emit_event(self, comp, kind, data=None):
        event = kind(data, source=[self])
        return comp.answer(event)

    def handle_event(self, comp, event):

        local_res = None
        local_handler = getattr(self, 'on_event', None)
        if local_handler:
            local_res = local_handler(comp, event)
        # bubble up in any case
        event.append(self)
        upper_res = comp.answer(event)
        # return local result in priority
        return local_res or upper_res


class Event(object):
    """Can be derived"""

    def __init__(self, data, source=[]):
        """
        `data` is a payload specific to the kind of event.
        `source` is a list of component business objects. The first one is the emitter.
        Each traversed component must append itself with `append` (see below).
        """

        self._source = source
        self.data = data

    @property
    def source(self):
        return self._source.copy()

    @property
    def emitter(self):
        return self._source[0]

    @property
    def last_relay(self):
        return self._source[-1]

    def is_(self, kind):
        return type(self) is kind

    def is_kind_of(self, kind):
        return isinstance(self, kind)

    def append(self, relay):
        self._source.append(relay)

    def cast_as(self, sub_kind):
        #assert(issubclass(sub_kind, self.__class__))
        return sub_kind(self.data, self._source)


# Standard events

class ColumnDeleted(Event):
    """
    The user clicked on the 'delete column' action.
    `data` is the column component (component.Component).
    """
    pass


class CardClicked(Event):
    """
    The user clicked on a card.
    `data` is the card component (component.Component)
    """
    pass


class PopinClosed(Event):
    """
    The Popin has closed.
    `data` is the component.Component containing the Popin.
    """
    pass


class CardEditorClosed(PopinClosed):
    """
    In the particular case when the Popin contains the card editor.
    `data` is the component.Component containing the Popin.
    """
    pass


class CardArchived(Event):
    """
    The user clicked on the `Delete` button in the card editor.
    No payload.
    """
    pass


class SearchIndexUpdated(Event):
    """
    Some operations have been committed on the search index.
    No payload.
    """
    pass


class CardDisplayed(Event):
    """
    A card has just been (re-)displayed on the board (default form).
    No payload.
    """
    pass


class BoardAccessChanged(Event):
    """
    The access conditions to the board changed.
    """


class BoardDeleted(BoardAccessChanged):
    """
    The board has been (or is about to be) deleted.
    No payload.
    """


class BoardArchived(BoardAccessChanged):
    """
    The board has been archived.
    No payload.
    """


class BoardRestored(BoardAccessChanged):
    """
    The board has been restored from archive.
    """


class BoardLeft(BoardAccessChanged):
    """
    The user has left the board.
    No payload.
    """


# "Request" events
class ParentTitleNeeded(Event):
    """The emitter needs context from parent in the form of a title string."""
    pass


class NewTemplateRequested(Event):
    """
    The user requested that a new template is created from the emitter.
    Payload is tuple (template_title, template_description, shared_flag).
    The receiver returns a new Template on success.
    """
    pass
