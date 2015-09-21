# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --
import peak
import json

import calendar
from datetime import datetime

from nagare import presentation, var, security, component, ajax, i18n
from nagare.i18n import _

from kansha.card.comp import CardFlow
from kansha.card.comp import CardWeightEditor

from .comp import Card, NewCard, CardTitle
from .comp import WEIGHTING_FREE, WEIGHTING_LIST


@peak.rules.when(ajax.py2js, (Card,))
def py2js(value, h):
    due_date = ajax.py2js(value.due_date(), h)
    if due_date:
        return u'{title:%s, editable:true, allDay: true, start: %s}' % (
            ajax.py2js(value.get_title(), h).decode('utf-8'), due_date)
    else:
        return None


@presentation.render_for(Card, model='edit')
def render_card_edit(self, h, comp, *args):
    """Render card in edition mode"""
    # Test for delete card
    if self.data is None:
        return h.root
    h << h.script('''YAHOO.kansha.app.hideOverlay();''')
    with h.div(class_='card-edit-form'):
        with h.div(class_='header row-fluid'):
            with h.div(class_='span12'):
                self.title.on_answer(lambda v: self.title.call(model='edit' if not self.title.model else None))
                h << h.AsyncRenderer().div(self.title, component.Component(self.column, 'title'), class_="async-title")
        with h.div(class_='row-fluid'):
            with h.div(class_='span9'):
                h << self.labels.render(h.AsyncRenderer(), model='edit')
                h << self.description.render(h.AsyncRenderer())
                h << self.gallery
                h << self.checklists
                h << h.hr
                h << comp.render(h.AsyncRenderer(), 'comments_flow')
            h << comp.render(h, "actions")
    return h.root


@presentation.render_for(Card, 'calendar')
def render(self, h, comp, *args):
    card = ajax.py2js(self, h)
    if card:
        clicked_cb = h.a.action(
            lambda: comp.answer(comp)
        ).get('onclick')

        dropped_cb = h.a.action(
            ajax.Update(
                action=self.new_start_from_ajax,
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


@presentation.render_for(Card, 'comments_flow')
def render_Card_comments_flow(self, h, comp, model):
    h << self.comments.render(h, model='header')
    h << self.flow.render(h.AsyncRenderer())
    return h.root


@presentation.render_for(Card, model='actions')
def render_card_actions(self, h, comp, *args):
    with h.div(class_='span2 cardactions'):
        with h.form:
            with h.ul():
                with h.li(class_="buttonAddChecklist"):
                    h << self.checklists.render(h, 'button')
                with h.li(class_="buttonAddFile"):
                    h << self.gallery.render(h, 'download')
                with h.li(class_="buttonVote"):
                    h << self.votes.render(h.AsyncRenderer(), 'edit')
                with h.li(class_="buttonDueDate"):
                    h << self.due_date.render(h.AsyncRenderer(), 'button')
                with h.li(class_="buttonDeleteCard"):
                    if security.has_permissions('edit', self) and not self.column.is_archive:
                        action = h.a.action(lambda: comp.answer('delete')).get('onclick')
                        close_func = 'function (){%s;}' % (action)
                        h << h.button(h.i(class_='icon-remove icon-grey'),
                                      _('Delete'),
                                      class_='btn btn-small',
                                      onclick=("if (confirm(\"%(confirm_msg)s\"))"
                                               " { YAHOO.kansha.app.archiveCard(%(close_func)s, '%(id)s', '%(col_id)s', '%(archive_col_id)s'); }return false;" %
                                               dict(close_func=close_func, id=self.id, col_id=self.column.id,
                                                    archive_col_id=self.column.board.archive_column.id,
                                                    confirm_msg=_(u'This card will be deleted. Are you sure?'))))
                if self.board.weighting_cards:
                    with h.li(class_="actionWeight"):
                        h << self._weight.on_answer(lambda v: self._weight.call(model='edit_weight' if v else None))
                h << comp.render(h, 'members')

    return h.root


@presentation.render_for(Card, 'dnd')
def render_card_dnd(self, h, comp, *args):
    """DnD wrapping of the card"""
    if self.data is not None:
        id_ = h.generate_id('dnd')
        with h.div(id=id_):
            h << comp.render(h.AsyncRenderer())
            h << h.script('YAHOO.kansha.dnd.initCard("%s")' % id_)
    return h.root


@presentation.render_for(CardWeightEditor)
def render_cardweighteditor(self, h, comp, *args):
    h << h.a(h.i(class_='icon-star icon-grey'), self.weight, class_='btn btn-small').action(
        lambda: comp.call(self, model='edit'))
    return h.root


@presentation.render_for(CardWeightEditor, 'edit')
def render_cardweighteditor_edit(self, h, comp, *args):
    def answer():
        if self.commit():
            comp.answer()

    if self.board.weighting_cards == WEIGHTING_FREE:
        with h.form:
            h << h.input(value=self.weight(), type='text').action(self.weight).error(self.weight.error)
            h << h.button(_('Save'), class_='btn btn-primary btn-small').action(answer)

    elif self.board.weighting_cards == WEIGHTING_LIST:
        with h.form:
            with h.div(class_='btn select'):
                with h.select.action(self.weight):
                    for value in self.board.weights.split(','):
                        h << h.option(value, value=value).selected(self.weight)
            h << h.button(_('Save'), class_='btn btn-primary btn-small').action(answer)

    return h.root


@presentation.render_for(Card, 'no_dnd')
def render_card_no_dnd(self, h, comp, *args):
    """No DnD wrapping of the card"""
    h << comp.render(h.AsyncRenderer())
    return h.root


@presentation.render_for(Card, 'new')
def render_card_new(self, h, comp, *args):
    h << comp.becomes(self, None)
    h << h.script('''card = YAHOO.util.Dom.get('%s');
    list = YAHOO.util.Dom.getAncestorByClassName(card, 'list-body');
    list.scrollTop = card.offsetTop - list.offsetTop;''' % self.id)
    return h.root


@presentation.render_for(Card)
def render(self, h, comp, *args):
    """Render the card"""
    card_id = h.generate_id()

    onclick = h.a.action(lambda: comp.answer(comp)).get('onclick').replace('return', "")
    if self.column.board.card_matches:
        c_class = 'card highlight' if self.id in self.column.board.card_matches else 'card hidden'
    else:
        c_class = 'card'
    with h.div(id=self.id, class_= c_class):
        h << {
            'onmouseover': "YAHOO.kansha.app.highlight(this, 'badges', false);YAHOO.kansha.app.highlight(this, 'members', false);",
            'onmouseout': "YAHOO.kansha.app.highlight(this, 'badges', true);YAHOO.kansha.app.highlight(this, 'members', true);"}
        with h.div(id=card_id, onclick=onclick):
            h << self.labels
            h << self.title.render(h, 'card-title')
            if self.has_cover():
                h << h.p(component.Component(self.get_cover(), model='cover'), class_='cover')
            h << comp.render(h, 'badges')
            if security.has_permissions('edit', self):
                h << comp.render(h, 'members')
            else:
                h << comp.render(h, 'members_read_only')

    reload_card = h.a.action(ajax.Update()).get('onclick')
    h << h.script("""YAHOO.kansha.reload_cards['%s']=function() {%s}""" % (self.id, reload_card))
    return h.root


@presentation.render_for(Card, model='readonly')
def render(self, h, comp, *args):
    """Render the card read-only"""
    card_id = h.generate_id()
    onclick = '%s#id_%s' % (self.data.column.board.url, self.id)
    with h.div(id=self.id, class_='card'):
        h << {
            'onmouseover': "YAHOO.kansha.app.highlight(this, 'badges', false);YAHOO.kansha.app.highlight(this, 'members', false);",
            'onmouseout': "YAHOO.kansha.app.highlight(this, 'badges', true);YAHOO.kansha.app.highlight(this, 'members', true);"}
        with h.div(id=card_id, onclick="window.location.href='%s'" % onclick):
            h << self.labels
            h << self.title.render(h, 'card-title')
            if self.has_cover():
                h << h.p(component.Component(self.get_cover(), model='cover'), class_='cover')
            h << comp.render(h, 'badges')
            h << comp.render(h, 'members_read_only')

    return h.root


@presentation.render_for(Card, model='badges')
def render_card_badges(self, h, comp, *args):
    """Render card badges in summary view"""
    with h.div(class_='badges'):
        h << self.checklists.render(h, model='badge')
        h << self.votes.render(h, model='badge')
        h << self.due_date.render(h, model='badge')
        h << self.description.render(h, model='badge')
        h << self.comments.render(h, model='badge')
        h << self.gallery.render(h, model='badge')
        if self.weight:
            label = _('weight')
            h << h.span(h.i(class_='icon-star icon-grey'), ' ', self.weight, class_='label', data_tooltip=label)
    return h.root


@presentation.render_for(Card, model='members')
def render_card_members(self, h, comp, *args):
    """Member section view for card

    First members icons,
    Then icon "more user" if necessary
    And at the end icon "add user"
    """
    with h.div(class_='members'):
        h << h.script('''YAHOO.kansha.app.hideOverlay();''')
        for m in self.members[:self.max_shown_members]:
            h << m.on_answer(self.remove_member).render(h, model="overlay-remove")
        if len(self.members) > self.max_shown_members:
            h << h.div(self.see_all_members, class_='more')
        h << h.div(self.overlay_add_members, class_='add')
    return h.root


@presentation.render_for(Card, model='members_read_only')
def render_card_members_read_only(self, h, comp, *args):
    """Member section view for card

    First members icons,
    Then icon "more user" if necessary
    And at the end icon "add user"
    """
    with h.div(class_='members'):
        for m in self.members[:self.max_shown_members]:
            member = m.render(h, "avatar")
            member.attrib.update({'class': 'miniavatar unselectable'})
            h << member
        if len(self.members) > self.max_shown_members:
            h << h.div(self.see_all_members, class_='more')
    return h.root


@presentation.render_for(Card, "members_list_overlay")
def render_members_members_list_overlay(self, h, comp, *args):
    """Overlay to list all members"""
    h << h.h2(_('All members'))
    with h.form:
        with h.div(class_="members"):
            if security.has_permissions('edit', self):
                h << [m.on_answer(comp.answer).render(h, "remove") for m in self.members]
            else:
                h << [m.render(h, "avatar") for m in self.members]
    return h.root


@presentation.render_for(Card, "add_member_overlay")
def render_members_add_member_overlay(self, h, comp, *args):
    """Overlay to add member"""
    h << h.h2(_('Add members'))
    if self.favorites:
        with h.div(class_="favorites"):
            h << h.h3(_('Suggestions'))
            with h.ul():
                h << h.li(self.favorites)
    with h.div(class_="members search"):
        h << self.new_member
    return h.root


@presentation.render_for(NewCard)
def render_new_card(self, h, comp, *args):
    """Render card creator minified"""
    h << h.a(h.strong('+'), h.span(_('Add a card')),
             class_='link-small').action(lambda: comp.answer(comp.call(model='add')))
    if self.needs_refresh:
        h << h.script('increase_version();')
        self.toggle_refresh()
    return h.root


@presentation.render_for(NewCard, 'add')
def render_new_card_add(self, h, comp, *args):
    """Render card creator form"""
    text = var.Var()
    id_ = h.generate_id('newCard')

    def answer():
        self.toggle_refresh()
        comp.answer(text())

    with h.form(class_='card-add-form'):
        h << h.input(type='text', id=id_).action(text)
        h << h.button(_('Add'), class_='btn btn-primary btn-small').action(answer)
        h << ' '
        h << h.button(_('Cancel'), class_='btn btn-small').action(comp.answer)

    h << h.script("""document.getElementById('%s').focus(); """ % id_,
                  type="text/javascript", language="javascript")

    return h.root


@presentation.render_for(Card, model='flow')
def render_card_flow(self, h, comp, model, *args):
    with h.div(class_='comment'):
        with h.div(class_='left'):
            h << self.author.render(h, model='avatar')
        with h.div(class_='right'):
            h << self.author.render(h, model='fullname')
            h << _(' added this card ') << comp.render(h, 'creation_date')
    return h.root


@presentation.render_for(Card, model='creation_date')
def render_card_creation_date(self, h, comp, model, *args):
    span_id = h.generate_id()
    h << h.span(id=span_id, class_="date")

    utcseconds = calendar.timegm(datetime.utctimetuple(self.data.creation_date))

    h << h.script(
        "YAHOO.kansha.app.utcToLocal('%s', %s, '%s', '%s');" % (span_id, utcseconds, _(u'at'), _(u'on'))
    )

    return h.root


@presentation.render_for(CardTitle, 'card-title')
def render_card_title(self, h, comp, *args):
    """Render the title of the associated card"""
    h << h.a(self.text)
    return h.root


@presentation.render_for(CardFlow)
def render_cardflow(self, h, comp, model, *args):
    for e in self.elements:
        h << e.render(h, model='flow')
    h << component.Component(self.card).render(h, 'flow')
    return h.root
