# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from nagare.i18n import _
from nagare import ajax, component, presentation, security, var

from kansha import events

from .comp import Card, NewCard


@presentation.render_for(Card, 'no_dnd')
def render_card_no_dnd(self, h, comp, *args):
    """No DnD wrapping of the card"""
    return comp.render(h.AsyncRenderer())


@presentation.render_for(Card, 'new')
def render_card_new(self, h, comp, *args):
    h << comp.becomes(model=None)
    h << h.script(
        "card = YAHOO.util.Dom.get(%s);"
        "list = YAHOO.util.Dom.getAncestorByClassName(card, 'list-body');"
        "list.scrollTop = card.offsetTop - list.offsetTop;" %
        ajax.py2js(self.id)
    )
    return h.root


@presentation.render_for(Card)
def render(self, h, comp, *args):
    """Render the card"""

    extensions = self.extensions

    card_id = h.generate_id()

    onclick = h.a.action(self.emit_event, comp, events.CardClicked, comp).get('onclick').replace('return', "")
    with h.div(id=self.id, class_='card ' + self.card_filter(self)):
        with h.div(id=card_id, onclick=onclick):
            with h.div(class_='headers'):
                h << [extension.render(h, 'header') for _name, extension in extensions]
            with h.div(class_='covers'):
                with h.div(class_='title'):
                    h << self.title.render(h, 'readonly')
                h << [extension.render(h, 'cover') for _name, extension in extensions]
            with h.div(class_='badges'):
                h << [extension.render(h, 'badge') for _name, extension in extensions]
    if self.card_filter(self):
        h << component.Component(self.card_filter)

    h << h.script(
        "YAHOO.kansha.reload_cards[%s]=function() {%s}""" % (
            ajax.py2js(self.id),
            h.a.action(ajax.Update()).get('onclick')
        )
    )

    return h.root


@presentation.render_for(Card, model='readonly')
def render(self, h, comp, *args):
    """Render the card read-only"""
    with h.div(id=self.id, class_='card'):
        with h.div:
            with h.div(class_='title'):
                h << self.title.render(h, 'readonly')
            # FIXME: unify with main card view.
    return h.root


@presentation.render_for(Card, model='edit')
def render_card_edit(self, h, comp, *args):
    """Render card in edition mode"""
    # Test for delete card
    if self.data is None:
        return h.root

    parent_title = self.emit_event(comp, events.ParentTitleNeeded) or ''

    with h.div(class_='card-edit-form'):
        with h.div(class_='header'):
            with h.div(class_='title'):
                h << self.title.render(h.AsyncRenderer(), 0 if security.has_permissions('edit', self) else 'readonly')
                h << h.span('(%s)' % parent_title, class_='reminder')
        with h.div:
            with h.div(class_='card-actions'):
                h << comp.render(h, 'delete-action')
                h << [extension.render(h.AsyncRenderer(), 'action') for __, extension in self.extensions]
            with h.div(class_='card-edition'):
                for name, extension in self.extensions:
                    h << h.div(extension.render(h.AsyncRenderer()), class_=name)
        h << h.div(class_='clear')
    return h.root


@presentation.render_for(Card, 'delete-action')
def render_card_delete(self, h, comp, model):
    if security.has_permissions('edit', self) and not self.archived:
        with h.form:
            h << h.SyncRenderer().button(
                h.i(class_='icon-bin'),
                _('Delete'),
                onclick='return confirm(%s)' % ajax.py2js(
                    _(u'This card will be archived. Are you sure?')
                ).decode('UTF-8'),
                class_='btn delete').action(self.emit_event, comp, events.CardArchived)
    return h.root


@presentation.render_for(Card, 'calendar')
def render_in_calendar(self, h, comp, *args):
    # TODO should be in due_date extension
    due_date = dict(self.extensions)['due_date']().due_date
    if due_date:
        due_date = ajax.py2js(due_date, h)
        parent_title = self.emit_event(comp, events.ParentTitleNeeded) or ''
        card = u'{title:%s, editable:true, allDay: true, start: %s, _id: %s}' % (
            ajax.py2js(u'{} ({})'.format(self.data.title, parent_title), h).decode('utf-8'),
            due_date, ajax.py2js(self.id, h))
        clicked_cb = h.a.action(
            lambda: self.emit_event(comp, events.CardClicked, comp)
        ).get('onclick')

        dropped_cb = h.a.action(
            ajax.Update(
                action=self.card_dropped,
                render=lambda render: '',
                with_request=True
            )
        ).get('onclick')[:-2]

        h << h.script(u"""YAHOO.kansha.app.add_event($('#calendar'), %(card)s,
                         function() { %(clicked_cb)s},
                         function(start) { %(dropped_cb)s&start="+start);} )""" % {
            'card': card,
            'clicked_cb': clicked_cb,
            'dropped_cb': dropped_cb
        })

    return h.root


@presentation.render_for(Card, 'dnd')
def render_card_dnd(self, h, comp, *args):
    """DnD wrapping of the card"""
    if self.data is not None:
        id_ = h.generate_id('dnd')
        with h.div(id=id_, class_='card-dnd-wrapper'):
            h << comp.render(h.AsyncRenderer())
            h << h.script('YAHOO.kansha.dnd.initCard(%s)' % ajax.py2js(id_))
    return h.root


#####


@presentation.render_for(NewCard)
def render_new_card(self, h, comp, *args):
    """Render card creator minified"""
    h << h.a(h.strong('+'), h.span(_('Add a card')),
             class_='link-small').action(comp.becomes, model='add')
    if self.needs_refresh:
        h << h.script('increase_version();')
        self.toggle_refresh()
    return h.root


def toggle_answer(card_editor, comp, text):
    card_editor.toggle_refresh()
    comp.becomes(model=None)
    if text:
        comp.answer(text().strip())


@presentation.render_for(NewCard, 'add')
def render_new_card_add(self, h, comp, *args):
    """Render card creator form"""
    text = var.Var()
    id_ = h.generate_id('newCard')

    with h.form(class_='card-add-form'):
        h << h.input(type='text', id=id_).action(text)
        h << h.button(_('Add'), class_='btn btn-primary').action(toggle_answer, self, comp, text)
        h << ' '
        h << h.button(_('Cancel'), class_='btn').action(toggle_answer, self, comp, None)

    h << h.script("""document.getElementById(%s).focus(); """ % ajax.py2js(id_))

    return h.root
