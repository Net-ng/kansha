# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation, component
from nagare.i18n import _


class Popin(object):

    """Popin component"""

    panel_id = 0

    def __init__(self, comp, model):
        """Initialization

        In:
            - ``comp`` -- the component wrapped by the popin
            - ``model`` -- the model of the wrapped component used
                to populate the popin content
        """
        self.comp = component.Component(comp, model=comp.model)
        self.model = model

        Popin.panel_id += 1
        self.id = 'panel%d' % Popin.panel_id


@presentation.render_for(Popin, 'dnd')
@presentation.render_for(Popin, 'edit')
def render(self, h, comp, *args):
    return h.root


@presentation.render_for(Popin, 'calendar')
@presentation.render_for(Popin)
def render(self, h, comp, *args):
    """Render the popin and opens it"""

    action = h.a.action(lambda: comp.answer(self.comp)).get('onclick')
    close_func = 'function (){%s;}' % (action)

    h << self.comp

    with h.div(style='display: none'):
        with h.div(id=self.id):
            h << h.a(title=_('Close this dialog window.'),
                     class_='icon-remove icon-grey action-close popin-close',
                     onclick="YAHOO.kansha.app.closePopin()", href='#')
            self.comp.on_answer(comp.answer)
            h << self.comp.render(h.AsyncRenderer(), model=self.model)

    h << h.script('''YAHOO.kansha.app.showPopin(%r, %s);''' % (self.id, close_func))

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
