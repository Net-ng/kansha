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

from .comp import Title


@presentation.render_for(Title, 'tabname')
def render(self, h, comp, *args):
    h.head << h.head.title(self.text)
    return h.root


@presentation.render_for(Title)
def render(self, h, comp, *args):
    """Render the title of the associated object

    Used by column title and card title on popin
    """
    with h.div(class_='title'):
        kw = {}
        if not security.has_permissions('edit', self):
            kw['style'] = 'cursor: default'
        a = h.a(self.text, **kw)
        if security.has_permissions('edit', self):
            a.action(comp.answer)
        h << a
    return h.root


@presentation.render_for(Title, model='edit')
def render(self, h, comp, *args):
    """Render the title of the associated object"""
    text = var.Var(self.text)
    with h.form(class_='title-form'):
        id_ = h.generate_id()
        if self.field_type == 'textarea':
            h << h.textarea(self.text, id_=id_).action(text)
        elif self.field_type == 'input':
            h << h.input(type='text', value=self.text,
                         id_=id_).action(text)
        else:
            raise ValueError(_('Unsupported field_type %r') % self.field_type)
        h << h.button(_('Save'), class_='btn btn-primary btn-small').action(
            lambda: comp.answer(self.change_text(text())))
        h << ' '
        h << h.button(_('Cancel'), class_='btn btn-small').action(comp.answer)
        h << h.script('YAHOO.kansha.app.selectElement(%r);YAHOO.kansha.app.hideCardsLimitEdit(%s)' % (id_, self.parent.id))
    return h.root
