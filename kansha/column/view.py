# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.i18n import _
from nagare import ajax, presentation, security, var

from kansha.toolbox import popin

from .comp import CardsCounter, Column, NewColumnEditor


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
        "YAHOO.kansha.app.saveLimit(%(list_id)s, %(limit)s);" %
        {
            'list_id': ajax.py2js(self.id),
            'limit': ajax.py2js(self.nb_max_cards or 0)
        }
    )
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
                onclick = (
                    u"if (confirm(%(message)s)){"
                    u" YAHOO.kansha.app.hideOverlay();"
                    u" %(callback)s"
                    u"}" %
                    {
                        'message': ajax.py2js(
                            _(u'The list will be deleted. Are you sure?')
                        ).decode('UTF-8'),
                        'callback': h.a.action(
                            comp.answer, 'delete'
                        ).get('onclick')
                    }
                )
                h << h.a(_(u'Delete this list'), onclick=onclick)
            h << h.li(
                h.a(_('Set cards limit')).action(
                    comp.answer, 'set_limit'
                ),
                id=self.id + '_counter_option'
            )
        else:
            with h.li:
                onclick = "if (confirm(%(message)s)){%(purge_func)s;}" % {
                    'message': ajax.py2js(
                        _(u'All cards will be deleted. Are you sure?')
                    ).decode('UTF-8'),
                    'purge_func': h.a.action(
                        comp.answer, 'purge'
                    ).get('onclick')
                }
                h << h.a(_('Purge the cards'), onclick=onclick)

    return h.root


@presentation.render_for(Column, model='header')
def render_column_header(self, h, comp, *args):
    with h.div(class_='title'):
        h << self.title.render(h.AsyncRenderer(), 0 if security.has_permissions('edit', self) and not self.is_archive else 'readonly')
    h << self.card_counter
    return h.root


@presentation.render_for(Column, model='title')
def render_column_title(self, h, comp, *args):
    with h.div(class_='title'):
        h << self.title.render(h, 'readonly')
    return h.root


@presentation.render_for(Column, 'dnd')
def render_column_dnd(self, h, comp, *args):
    """DnD wrapper for column"""
    h << comp.render(h, None)
    h << h.script(
        "YAHOO.util.Event.onDOMReady(function() {"
        "  YAHOO.kansha.app.initList(%(list_id)s);"
        "  YAHOO.kansha.dnd.initList(%(list_id)s);"
        "  YAHOO.kansha.app.hideOverlay();"
        "})" % {'list_id': ajax.py2js(self.id)}
    )
    return h.root


@presentation.render_for(Column, 'body')
def render_column_body(self, h, comp, *args):
    model = 'dnd' if security.has_permissions('edit', self) else "no_dnd"
    id_ = h.generate_id()
    with h.div(class_='list-body', id=id_):
        h << [card.on_answer(self.handle_event, comp).render(h, model=model) for card in self.cards]
        h << h.script("YAHOO.kansha.dnd.initTargetCard(%s)" % ajax.py2js(id_))
    kw = {}
    if not security.has_permissions('edit', self):
        kw['style'] = 'width: 0px'
    if not self.is_archive:
        with h.div(class_='list-footer', id=self.id + '_footer', **kw):
            if security.has_permissions('edit', self):
                h << h.div(self.new_card.on_answer(self.ui_create_card, comp))

    h << h.script("YAHOO.kansha.app.countCards(%s)" % ajax.py2js(self.id))
    return h.root


@presentation.render_for(NewColumnEditor)
def render_NewColumnEditor(self, h, comp, *args):
    """Render column creator"""
    h << h.h2(_(u'Add list'))
    with h.form:
        with h.div:
            id_ = h.generate_id()
            h << h.label(_('Name'), for_=id)
            h << h.input(id=id_, type='text', placeholder=_('List title')).error(self.title.error).action(self.title)

        with h.div:
            id_ = h.generate_id()
            h << h.label(_('Position'), for_=id_)
            with h.select(id=id_).error(self.index.error).action(self.index):
                for i in xrange(1, self.columns_count + 2):
                    h << h.option(i, value=i - 1).selected(i)

        with h.div:
            id_ = h.generate_id()
            h << h.label(_('Number max of cards'), id_=id_)
            h << h.input(id=id_, type='text').error(self.nb_cards.error).action(self.nb_cards)
            h << h.script(
                """YAHOO.util.Event.on(%s, 'keyup', function (e) {
                        var result =this.value.replace(/[^0-9]/g, '')
                        if (this.value !=result) {
                               this.value = result;
                            }
                 })""" % ajax.py2js(id_)
            )

        with h.div(class_='buttons'):
            h << h.button(_('Add'), class_=('btn btn-primary')).action(self.commit, comp)
            h << ' '
            h << h.a(_('Cancel'), class_='btn').action(self.cancel, comp)
    return h.root


@presentation.render_for(CardsCounter)
def render_CardsCounter(self, h, comp, *args):
    with h.div(class_='list-counter'):
        self.error = None
        with h.div(class_='cardCounter', id=self.id):
            h << {'style': 'cursor: default'}
            h << h.span(self.text)
    h << h.script(
        "YAHOO.kansha.app.saveLimit(%(list_id)s, %(limit)s);"
        "YAHOO.kansha.app.countCards(%(list_id)s);" %
        {
            'list_id': ajax.py2js(self.column.id),
            'limit': ajax.py2js(self.column.nb_max_cards or 0)
        }
    )
    return h.root


@presentation.render_for(CardsCounter, model='edit')
def render_CardsCounter_edit(self, h, comp, *args):
    """Render the title of the associated object"""
    text = var.Var(self.text)
    with h.form(class_='title-form'):
        id_ = h.generate_id()
        h << h.input(id=id_, type='text', value=self.column.nb_max_cards or '').action(text)
        h << h.script(
            """YAHOO.util.Event.on(%s, 'keyup', function (e) {
                    var result =this.value.replace(/[^0-9]/g, '')
                    if (this.value !=result) {
                           this.value = result;
                        }
             });""" % ajax.py2js(id_)
        )
        h << h.button(_('Save'), class_='btn btn-primary').action(
            lambda: self.validate(text(), comp))
        h << ' '
        h << h.button(_('Cancel'), class_='btn').action(self.cancel, comp)
        if self.error is not None:
            with h.div(class_='nagare-error-message'):
                h << self.error
        h << h.script(
            "YAHOO.kansha.app.selectElement(%s);"
            "YAHOO.kansha.app.hideOverlay()" % ajax.py2js(id_)
        )
    return h.root
