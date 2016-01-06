#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation

from .comp import CardWeightEditor


@presentation.render_for(CardWeightEditor, 'action')
def render_cardweighteditor(self, h, comp, *args):
    if self.target.weighting_on():
        h << self.action_button
    return h.root


@presentation.render_for(CardWeightEditor, 'action_button')
def render_cardweighteditor_button(self, h, comp, *args):
    h << h.a(h.i(class_='icon-star'), self.weight, class_='btn').action(
            comp.call, self, model='edit')
    return h.root
