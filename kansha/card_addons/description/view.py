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
from nagare import presentation, var, security, ajax

from .comp import CardDescription


@presentation.render_for(CardDescription)
def render(self, h, comp, *args):
    """Render description component.

    If text is empty, display a text area otherwise it's a simple text
    """
    id_ = h.generate_id()
    kw = {'class': 'description', 'id': id_}
    if security.has_permissions('edit', self.card):
        kw['onclick'] = h.a.action(comp.becomes, model='edit').get('onclick')
    with h.div(**kw):
        if self.text:
            h << h.parse_htmlstring(self.text, fragment=True)
        elif security.has_permissions('edit', self.card):
            h << h.textarea(placeholder=_("Add description."))

    h << h.script("YAHOO.kansha.app.urlify($('#' + %s))" % ajax.py2js(id_))
    return h.root


def change_text(description, comp, text):
    description.change_text(text)
    comp.becomes(model=None)


@presentation.render_for(CardDescription, model='edit')
def render(self, h, comp, *args):
    """Render description component in edit mode"""
    text = var.Var(self.text)
    with h.div(class_="description"):
        with h.form(class_='description-form'):
            txt_id = h.generate_id()
            h << h.textarea(text(), id_=txt_id).action(text)

            with h.div(class_='buttons'):
                h << h.button(_('Save'), class_='btn btn-primary').action(lambda: change_text(self, comp, text()))
                h << ' '
                h << h.button(_('Cancel'), class_='btn').action(change_text, self, comp, None)
                h << h.script(
                    "YAHOO.kansha.app.init_ckeditor(%s, %s)" % (
                        ajax.py2js(txt_id),
                        ajax.py2js(security.get_user().get_locale().language)
                    )
                )
    return h.root


@presentation.render_for(CardDescription, model='badge')
def render(self, h, *args):
    """Render description component as a card badge"""
    if self.text:
        with h.span(class_='badge'):
            h << h.span(h.i(class_='icon-pencil'), class_='label')
    return h.root
