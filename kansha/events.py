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
        local_handler = getattr(self, 'on_event')
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
    pass


class CardClicked(Event):
    pass


class PopinClosed(Event):
    pass


class CardEditorClosed(PopinClosed):
    pass


class CardArchived(Event):
    pass


class SearchIndexModified(Event):
    pass
