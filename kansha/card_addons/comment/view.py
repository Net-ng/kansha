# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
from nagare.i18n import _, _N, format_datetime
from nagare import ajax, presentation, security, var

from .comp import Comments, Comment, Commentlabel


@presentation.render_for(Comment)
@presentation.render_for(Comment, model='flow')
def render_comment(self, h, comp, model, *args):
    with h.div(class_='comment'):
        with h.div(class_='left'):
            h << self.author.render(h, model='avatar')
        with h.div(class_='right'):
            h << self.author.render(h, model='fullname')
            h << ' ' << _('wrote') << ' '
            h << h.span(
                _(u'on'), ' ',
                format_datetime(self.creation_date),
                class_="date")
            if security.has_permissions('delete_comment', self):
                onclick = (
                    u"if (confirm(%(message)s)){%(action)s;}return false" %
                    {
                        'action': h.a.action(
                            comp.answer, comp
                        ).get('onclick'),
                        'message': ajax.py2js(
                            _(u'Your comment will be deleted. Are you sure?')
                        ).decode('UTF-8')
                    }
                )
                h << h.a(h.i(class_='icon-cross'), title=_('Delete'),
                         class_="comment-delete", onclick=onclick, href='')
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
    h << h.script("YAHOO.kansha.app.urlify($('#' + %s))" % ajax.py2js(id_))
    return h.root


@presentation.render_for(Commentlabel, model='edit')
def render_comment_label_form(self, h, comp, *args):
    """edit a comment """
    text = var.Var(self.text)
    with h.form:
        txt_id, buttons_id = h.generate_id(), h.generate_id()
        sub_id = h.generate_id()
        h << h.textarea(text(), class_='expanded', id_=txt_id).action(text)
        with h.div(class_='buttons', id=buttons_id):
            h << h.input(value=_("Save"), id=sub_id, type='submit',
                         class_="btn btn-primary").action(lambda: comp.answer(self.change_text(text())))
            h << ' '
            h << h.input(value=_("Cancel"), type='submit',
                         class_="btn").action(lambda: comp.answer(''))

    return h.root


@presentation.render_for(Comments, model='form')
def render_comments_form(self, h, comp, *args):
    """Add a comment to the current card"""
    if security.has_permissions('comment', self):
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
            h.head.javascript(
                h.generate_id(),
                'YAHOO.kansha.app.addCtrlEnterHandler(%s, %s)' % (
                    ajax.py2js(txt_id), ajax.py2js(sub_id)
                )
            )
            with h.div(id=buttons_id, class_="buttons hidden"):
                h << h.input(value=_("Save"), id=sub_id, type='submit',
                             class_="btn btn-primary").action(lambda: comp.answer(text()))
                h << ' '
                h << h.input(value=_("Cancel"), type='submit',
                             class_="btn").action(lambda: comp.answer(''))

    return h.root


@presentation.render_for(Comments, model='badge')
def render_comments_badge(self, h, *args):
    """Comment badge for the card"""
    num_comments = self.num_comments
    if num_comments:
        with h.span(class_='badge'):
            h << h.span(h.i(class_='icon-bubble2'), ' ', num_comments, class_='label')
    return h.root


@presentation.render_for(Comments)
def render(self, h, comp, *args):
    """Render card comments"""
    self.load_children()
    with h.div(class_='card-extension-comments'):
        h << h.div(comp.render(h, "badge"), class_='nbItems')
        h << comp.on_answer(self.add).render(h, 'form') << h.hr
        h << self.comments

    return h.root
