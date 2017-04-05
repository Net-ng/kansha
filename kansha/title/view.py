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
from nagare import presentation, var

from .comp import EditableTitle, Title


@presentation.render_for(Title)
def render_title(self, h, comp, model):
    title = self.title()
    if title is not None and len(title) < 5:
        title += u' ' * (5 - len(title)) # unbreakable spaces ; when display-block is NOT an option
    with h.a(class_=self.class_, title=title).action(comp.answer):
        h << (h.input(placeholder=self.placeholder) if (self.placeholder and title is None) else title)

    return h.root


@presentation.render_for(Title, 'readonly')
def render_title_ro(self, h, *args):
    return h.span(self.title() or '', class_=self.class_)


@presentation.render_for(Title, 'edit')
def render_title_edit(self, h, comp, *args):
    title = var.Var(self.title() or '')
    id_ = h.generate_id('id')

    with h.form(class_=self.class_ + '-form'):
        input = (h.textarea(title, style='height: %dpx' % self.height) if self.height else h.input(value=title))
        h << input(id=id_, placeholder=self.placeholder).action(title)

        h << h.button(_('Save'), class_='btn btn-primary').action(self.set_title, comp, title)
        h << ' '
        h << h.button(_('Cancel'), class_='btn').action(comp.answer)

        h << h.script('YAHOO.kansha.app.selectElement(%s);' % id_)

    return h.root


@presentation.render_for(EditableTitle, 'readonly')
def render_editabletitle_ro(self, h, *args):
    return self.title.render(h, 'readonly')
