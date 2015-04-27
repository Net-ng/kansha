# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from .comp import Comments, Comment, Commentlabel
from nagare import presentation, security, var
from nagare.i18n import _, _N


@presentation.render_for(Comments, model='header')
def render(self, h, comp, *args):
    """Render card comments"""
    h << h.div(comp.render(h, "badge"), class_="nbItems")
    h << comp.on_answer(self.add).render(h, "form")
    #h << self.comments

    return h.root


@presentation.render_for(Comment)
@presentation.render_for(Comment, model='flow')
def render_comment(self, h, comp, model, *args):
    with h.div(class_='comment'):
        with h.div(class_='left'):
            h << self.author.render(h, model='avatar')
        with h.div(class_='right'):
            h << self.author.render(h, model='fullname')
            h << _(' wrote ')
            h << comp.render(h, 'creation_date')
            if security.has_permissions('delete_comment', self):
                h << h.a(_('Delete'),
                         class_="delete").action(lambda: comp.answer(comp))
            h << self.comment_label.render(h.AsyncRenderer())
    return h.root


@presentation.render_for(Commentlabel)
def render_for_comment_label(self, h, comp, *args):
    """Render the text  of the associated comment

    """
    id_ = h.generate_id()
    with h.div(id=id_, class_='text'):
        a = h.div([h.p(part) if part else h.br for part in self.text.split('\n')])
        if security.has_permissions('edit_comment', self):
            with a:
                h << {'onclick': h.a.action(comp.answer).get('onclick')}
        h << a
    h << h.script("""YAHOO.kansha.app.urlify($('#%s'))""" % id_)
    return h.root


@presentation.render_for(Commentlabel, model='edit')
def render_comment_label_form(self, h, comp, *args):
    """edit a comment """
    text = var.Var(self.text)
    with h.form:
        txt_id, buttons_id = h.generate_id(), h.generate_id()
        sub_id = h.generate_id()
        h << h.textarea(text(), class_='expanded', id_=txt_id).action(text)
        with h.div(id=buttons_id):
            h << h.input(value=_("Save"), id=sub_id, type='submit',
                         class_="btn btn-primary btn-small").action(lambda: comp.answer(self.change_text(text())))
            h << ' '
            h << h.input(value=_("Cancel"), type='submit',
                         class_="btn btn-small").action(lambda: comp.answer(''))

    return h.root


@presentation.render_for(Comments, model='form')
def render_comments_form(self, h, comp, *args):
    """Add a comment to the current card"""
    if security.has_permissions('comment', self.parent):
        text = var.Var()
        with h.form:
            txt_id, buttons_id = h.generate_id(), h.generate_id()
            sub_id = h.generate_id()
            kw = {
                "id": txt_id,
                "placeholder": _("Add comment."),
                "onfocus": "YAHOO.kansha.app.show('%s', true);YAHOO.util.Dom.addClass(this, 'expanded'); " % buttons_id,
            }
            h << h.textarea(**kw).action(text)
            h.head.javascript(h.generate_id(), 'YAHOO.kansha.app.addCtrlEnterHandler(%r, %r)' % (txt_id, sub_id))
            with h.div(id=buttons_id, class_="hidden"):
                h << h.input(value=_("Save"), id=sub_id, type='submit',
                             class_="btn btn-primary btn-small").action(lambda: comp.answer(text()))
                h << ' '
                h << h.input(value=_("Cancel"), type='submit',
                             class_="btn btn-small").action(lambda: comp.answer(''))

    return h.root


@presentation.render_for(Comments, model='badge')
def render_comments_badge(self, h, *args):
    """Comment badge for the card"""
    if self.comments:
        label = _N('comment', 'comments', len(self.comments))
        h << h.span(h.i(class_='icon-comment icon-grey'), ' ', len(self.comments), class_='label', data_tooltip=label)
    return h.root
