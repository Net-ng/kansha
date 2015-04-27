# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation, var, security
from nagare.i18n import _

from .comp import Description


@presentation.render_for(Description)
def render(self, h, comp, *args):
    """Render description component.

    If text is empty, display a text area otherwise it's a simple text
    """
    id_ = h.generate_id()
    kw = {'class': 'description', 'id': id_}
    if security.has_permissions('edit', self.parent):
        kw['onclick'] = h.a.action(
            lambda: self.change_text(comp.call(model='edit'))).get('onclick')
    with h.div(**kw):
        if self.text:
            h << [h.p(part) if part else h.br for part in self.text.split('\n')]
        elif security.has_permissions('edit', self.parent):
            h << h.textarea(placeholder=_("Add description."))

    h << h.script("""YAHOO.kansha.app.urlify($('#%s'))""" % id_)
    return h.root


@presentation.render_for(Description, model='edit')
def render(self, h, comp, *args):
    """Render description component in edit mode"""
    text = var.Var(self.text)
    with h.div(class_="description"):
        with h.form(class_='description-form'):
            txt_id, btn_id, buttons_id = h.generate_id(
            ), h.generate_id(), h.generate_id()
            h << h.textarea(text(), id_=txt_id, placeholder=_("Add description."),
                            onfocus="YAHOO.kansha.app.show('%s', true);" % buttons_id,
                            class_="expanded", style="resize:none").action(text)
            with h.div(id=buttons_id, class_="hidden"):
                h << h.button(_('Save'), class_='btn btn-primary btn-small',
                              id=btn_id).action(lambda: comp.answer(text()))
                h << ' '
                h << h.button(
                    _('Cancel'), class_='btn btn-small').action(comp.answer)

            h.head.javascript(h.generate_id(), 'YAHOO.kansha.app.addCtrlEnterHandler(%r, %r)' % (txt_id, btn_id))
            h.head.javascript(
                h.generate_id(), 'YAHOO.kansha.app.autoHeight(%r)' % (txt_id))

        # Put the focus on the text area
        h << h.script("""document.getElementById('%s').focus()""" %
                      txt_id, type="text/javascript", language="javascript")

    return h.root


@presentation.render_for(Description, model='badge')
def render(self, h, *args):
    """Render description component as a card badge"""
    if self.text:
        h << h.span(h.i(class_='icon-pencil icon-grey'), class_='label', data_tooltip=_('This %s has a description') % _(self.type))
    return h.root
