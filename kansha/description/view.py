# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation, var, security, ajax
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
            h << h.parse_htmlstring(self.text, fragment=True)
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
            txt_id = h.generate_id()
            h << h.textarea(text(), id_=txt_id).action(text)

            with h.div(class_='buttons'):
                h << h.button(_('Save'), class_='btn btn-primary btn-small').action(lambda: comp.answer(text()))
                h << ' '
                h << h.button( _('Cancel'), class_='btn btn-small').action(comp.answer)
                h << h.script('YAHOO.kansha.app.init_ckeditor(%s, %s)' % (ajax.py2js(txt_id), ajax.py2js(security.get_user().get_locale().language)))
    return h.root


@presentation.render_for(Description, model='badge')
def render(self, h, *args):
    """Render description component as a card badge"""
    if self.text:
        h << h.span(h.i(class_='icon-pencil icon-grey'), class_='label', data_tooltip=_('This %s has a description') % _(self.type))
    return h.root
