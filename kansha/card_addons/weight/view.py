#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.i18n import _
from nagare import ajax, presentation

from .comp import CardWeightEditor


def answer(editor, comp):
    if editor.commit():
        comp.answer()


@presentation.render_for(CardWeightEditor, 'action')
def render_cardweighteditor(self, h, comp, *args):
    if self.weighting_switch:
        h << self.action_button
    return h.root


@presentation.render_for(CardWeightEditor, 'action_button')
def render_CardWeightEditor_action_button(self, h, comp, *args):
    self.weight(str(self.data.weight))
    h << h.a(h.i(class_='icon-star-empty'), self.data.weight, class_='btn').action(
             comp.call, self, model='edit')
    return h.root


@presentation.render_for(CardWeightEditor, 'edit')
def render_CardWeightEditor_edit(self, h, comp, *args):
    if self.weighting_switch == self.WEIGHTING_FREE:
        id_ = h.generate_id('weight')
        with h.form:
            h << h.input(
                value=self.weight(),
                type='text',
                id_=id_).action(self.weight).error(self.weight.error)
            h << h.button(_('Save'), class_='btn btn-primary').action(answer, self, comp)
            h << h.script("""document.getElementById(%s).focus(); """ % ajax.py2js(id_))
    elif self.weighting_switch == self.WEIGHTING_LIST:
        with h.form:
            with h.div(class_='btn select'):
                with h.select.action(self.weight):
                    for value in self.allowed_weights.split(','):
                        h << h.option(value, value=value.strip()).selected(self.weight())
            h << h.button(_('Save'), class_='btn btn-primary').action(answer, self, comp)

    return h.root


@presentation.render_for(CardWeightEditor, 'badge')
def render_CardWeightEditor_badge(self, h, comp, *args):
    if self.data.weight:
        with h.span(class_='badge'):
            h << h.span(h.i(class_='icon-star-empty'), ' ',
                        self.data.weight, class_='label', title=_(u'Weight'))
    return h.root
