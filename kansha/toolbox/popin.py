# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import ajax
from nagare import presentation, component

from kansha.events import PopinClosed, EventHandlerMixIn


#TODO: replace Popin by Modal everywhere.

class Popin(EventHandlerMixIn):

    """Popin component"""

    panel_id = 0

    def __init__(self, comp, model):
        """Initialization

        In:
            - ``comp`` -- the component wrapped by the popin
            - ``model`` -- the model of the wrapped component used
                to populate the popin content
        """
        self.comp = component.Component(comp)
        self.model = model

        Popin.panel_id += 1
        self.id = 'panel%d' % Popin.panel_id

    def get_business_object(self):
        business_obj = self.comp()
        while isinstance(business_obj, Popin):
            # nested popins can happen when the user clicks too fast
            self.comp = business_obj.comp
            business_obj = self.comp()
        return business_obj

@presentation.render_for(Popin, 'dnd')
@presentation.render_for(Popin, 'edit')
def render(self, h, comp, *args):
    return h.root


@presentation.render_for(Popin, 'calendar')
@presentation.render_for(Popin)
def render(self, h, comp, model):
    """Render the popin and opens it"""
    business_obj = self.get_business_object()
    emit_event = getattr(business_obj, 'emit_event', self.emit_event)
    action = h.a.action(emit_event, comp, PopinClosed, comp).get('onclick')
    close_func = 'function (){%s;}' % (action)

    h << self.comp.on_answer(lambda x: None).render(h, model=model) # Ignore answers from this view

    with h.div(style='display: none'):
        with h.div(id=self.id):
            self.comp.on_answer(self.handle_event, comp)  # Popin is transparent
            h << self.comp.render(h.AsyncRenderer(), model=self.model)

    h << h.script(
        "YAHOO.kansha.app.showPopin(%s, %s)" % (ajax.py2js(self.id), close_func)
    )

    return h.root


class Modal(object):
    def __init__(self, comp, force_refresh=False):
        if not isinstance(comp, component.Component):
            comp = component.Component(comp)
        self.comp = comp
        self.force_refresh = force_refresh
        self.plugged = False

    def plug(self, comp):
        if not self.plugged:
            self.comp.on_answer(comp.answer)
            self.plugged = True


@presentation.render_for(Modal)
def render_PopinV2(self, h, comp, model):
    self.plug(comp)
    with h.div(class_='modal', id_='modal'):
        with h.div:
            if self.force_refresh:
                h << self.comp.render(h.SyncRenderer())
            else:
                h << self.comp
    if self.force_refresh:
        h << h.script('''$("#modal").click(function(e) {
        if ($(e.target).hasClass('modal')) {
            window.location = "%s";
        }
    });''' % h.SyncRenderer().a.action(comp.answer).get('href'))
    else:
        h << h.script('''$("#modal").click(function(e) {
        if ($(e.target).hasClass('modal')) {
           %s;
        }
    });''' % h.a.action(comp.answer).get('onclick'))
    return h.root


class Empty(object):

    """A component showing only a bit of Javascript
    """

    def __init__(self, js=None):
        """Initialization

        In:
            - ``js`` -- the javascript code to render
        """
        self.js = js


@presentation.render_for(Empty)
def render(self, h, comp, *args):
    """Render the js code"""
    if self.js is not None:
        h.head.javascript(h.generate_id(), self.js)
    h << ' '
    return h.root
