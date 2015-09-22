# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
import peak

from nagare import presentation, security, var, ajax
from nagare.i18n import _
from .comp import Column, NewColumn, ColumnTitle, CardsCounter
from ..toolbox import remote


@presentation.render_for(Column)
def render(self, h, comp, *args):
    """Render the column"""
    # Add answer on delete overlay component

    self.actions_comp.on_answer(lambda data, comp=comp: self.actions(data, comp))
    column_class = 'span-auto list'
    if self.is_archive:
        column_class += ' archive'
    with h.div(class_=column_class, id=self.id, ):
        with h.div(class_='list-header', id=self.id + '_header'):
            with h.div(class_='list-title', id=self.id + '_title'):
                h << comp.render(h.AsyncRenderer(), 'header')
            with h.div(class_='list-actions hidden'):
                if security.has_permissions('edit', self):
                    h << self.actions_overlay
        h << comp.render(h.AsyncRenderer(), 'body')
    h << h.script(
        "YAHOO.kansha.app.saveLimit('%(list_id)s', %(limit)i);" % dict(list_id=self.id, limit=self.nb_max_cards or 0))
    return h.root


@presentation.render_for(Column, 'calendar')
def render(self, h, comp, *args):
    return [card.render(h, 'calendar') for card in self.cards]


@presentation.render_for(Column, 'new')
def render_column_new(self, h, comp, *args):
    return h.div(comp.becomes(self, 'dnd'), class_='new')


@presentation.render_for(Column, model='overlay')
def render_column_overlay(self, h, comp, *args):
    """Render the column menu"""
    with h.ul(class_='nav nav-list'):
        if not self.is_archive:
            with h.li:
                onclick = u"if (confirm('%(message)s')){YAHOO.kansha.app.hideOverlay();%(callback)s;}" % {
                    'message': _(u'The list will be deleted. Are you sure?'),
                    'callback': h.a.action(lambda: comp.answer(('delete', self.data.id))).get('onclick')}
                h << h.a(_(u'Delete this list'), onclick=onclick)
            h << h.li(h.a(
                _('Set cards limit')).action(lambda: comp.answer(('set_limit', self.data.id))),
                      id=self.id + '_counter_option')
        else:
            with h.li:
                action = h.a.action(lambda: comp.answer(('purge', self.data.id))).get('onclick')
                onclick = "if (confirm(\"%(confirm_msg)s\")){%(purge_func)s;}"
                onclick = onclick % dict(purge_func=action, confirm_msg=_(u'All cards will be deleted. Are you sure?'))
                h << h.a(_('Purge the cards'), onclick=onclick)

    return h.root


@presentation.render_for(Column, model='header')
def render_column_header(self, h, comp, *args):
    if self.card_counter.model != 'edit':
        h << self.title
    if self.title.model != 'edit':
        h << self.card_counter
    return h.root


@presentation.render_for(Column, model='title')
def render_column_title(self, h, comp, *args):
    h << self.title.render(h, 'no-edit')
    return h.root


@presentation.render_for(Column, 'dnd')
def render_column_dnd(self, h, comp, *args):
    """DnD wrapper for column"""
    h << comp.render(h, None)
    h << h.script('''YAHOO.util.Event.onDOMReady(function() {
      YAHOO.kansha.app.initList(%(list_id)r);
      YAHOO.kansha.dnd.initList(%(list_id)r);
      YAHOO.kansha.app.hideOverlay();
    });''' % {'list_id': self.id})
    return h.root


@presentation.render_for(Column, 'body')
def render_column_body(self, h, comp, *args):
    model = 'dnd' if security.has_permissions('edit', self) else "no_dnd"
    id_ = h.generate_id()
    with h.div(class_='list-body', id=id_):
        h << [card.on_answer(self.edit_card).render(h, model=model) for card in self.cards]
        h << h.script("YAHOO.kansha.dnd.initTargetCard('%s')" % id_)
    kw = {}
    if not security.has_permissions('edit', self):
        kw['style'] = 'width: 0px'
    if not self.is_archive:
        with h.div(class_='list-footer', id=self.id + '_footer', **kw):
            if security.has_permissions('edit', self):
                h << h.div(self.new_card)

    h << h.script("YAHOO.kansha.app.countCards(%(list_id)s);" % dict(list_id=self.id))
    return h.root


@presentation.render_for(ColumnTitle)
def render_ColumnTitle(self, h, comp, *args):
    """Render the title of the associated object

    Used by column title and card title on popin
    """
    with h.div(class_='title'):
        kw = {}
        if not security.has_permissions('edit', self):
            kw['style'] = 'cursor: default'
        a = h.a(self.text, title=self.text, **kw)
        if security.has_permissions('edit', self):
            a.action(comp.answer)
        h << a
    h << h.script('YAHOO.kansha.app.showCardsLimitEdit(%s)' % self.parent.id)
    return h.root


@presentation.render_for(ColumnTitle, model='no-edit')
def render_ColumnTitle_no_edit(self, h, comp, *args):
    h << h.div('(%s) ' % self.text, class_='in-list')
    return h.root


@presentation.render_for(NewColumn)
def render_newcolumn(self, h, comp, *args):
    """Render column creator"""
    id_ = h.generate_id('newColumn')
    with h.form:
        h << h.label(_('Name'))
        h << h.input(id=id_, type='text', placeholder=_(
            'List title')).action(self.title)
        h << h.label(_('Position'))
        with h.select().action(lambda v: self.index(int(v))):
            for i in xrange(1, self.count_board_columns() + 2):
                h << h.option(i, value=i - 1).selected(i)
        h << self.nb_cards_comp
        with h.div:
            h << h.button(_('Add'), class_=('btn btn-primary btn-small'),
            ).action(remote.Action(lambda: self.create_column(comp)))
            h << ' '
            h << h.button(_('Cancel'), class_='btn btn-small').action(
                remote.Action(lambda: """YAHOO.kansha.app.hideOverlay()"""))
    return h.root


@presentation.render_for(NewColumn, 'nb_cards')
def render_newcolumn_nbcards(self, h, comp, *args):
    id_ = h.generate_id('Cardnumber')
    with h.form:
        h << h.label(_('Number max of cards'))
        h << h.input(id=id_, type='text').action(self.nb_cards)
        h << h.script("""YAHOO.util.Event.on("%s", 'keyup', function (e) {
                                var result =this.value.replace(/[^0-9]/g, '')
                                if (this.value !=result) {
                                       this.value = result;
                                    }
                         });""" % id_)
    return h.root


@presentation.render_for(CardsCounter)
def render_CardsCounter(self, h, comp, *args):
    with h.div(class_='list-counter'):
        self.error = None
        with h.div(class_='cardCounter', id=self.id):
            h << {'style': 'cursor: default'}
            h << h.span(self.text)
    h << h.script(
        "YAHOO.kansha.app.saveLimit('%(list_id)s', %(limit)i);YAHOO.kansha.app.countCards(%(list_id)s);" % dict(
            list_id=self.column.id, limit=self.column.nb_max_cards or 0))
    return h.root


@presentation.render_for(CardsCounter, model='edit')
def render_CardsCounter_edit(self, h, comp, *args):
    """Render the title of the associated object"""
    text = var.Var(self.text)
    with h.form(class_='title-form'):
        id_ = h.generate_id()
        h << h.input(id=id_, type='text', value=self.column.nb_max_cards or '').action(text)
        h << h.script("""YAHOO.util.Event.on("%s", 'keyup', function (e) {
                                var result =this.value.replace(/[^0-9]/g, '')
                                if (this.value !=result) {
                                       this.value = result;
                                    }
                         });""" % id_)
        h << h.button(_('Save'), class_='btn btn-primary btn-small').action(
            lambda: self.validate(text(), comp))
        h << ' '
        h << h.button(_('Cancel'), class_='btn btn-small').action(self.cancel, comp)
        if self.error is not None:
            with h.div(class_='nagare-error-message'):
                h << self.error
        h << h.script('YAHOO.kansha.app.selectElement(%r);YAHOO.kansha.app.hideOverlay()' % id_)
    return h.root
