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
from nagare import ajax, component, presentation, security, var

from kansha.toolbox import popin

from .comp import CardsCounter, Column, NewColumnEditor


@presentation.render_for(Column)
def render(self, h, comp, *args):
    """Render the column"""

    column_class = 'span-auto list'
    if self.is_archive:
        column_class += ' archive'
    with h.div(class_=column_class, id=self.id, ):
        h << comp.render(h.AsyncRenderer(), 'content')
    return h.root


@presentation.render_for(Column, 'content')
def render_content(self, h, comp, model):
    h << comp.render(h.AsyncRenderer(), 'header')
    h << comp.render(h, 'body')
    h << self.card_counter.render(h, 'footer')
    h << component.Component(self.card_filter, 'footer')
    return h.root


@presentation.render_for(Column, 'calendar')
def render_column_calendar(self, h, comp, *args):
    return [card.render(h.AsyncRenderer(), 'calendar') for card in self.cards]


@presentation.render_for(Column, 'new')
def render_column_new(self, h, comp, *args):
    return h.div(comp.becomes(self, 'dnd'), class_='new')


@presentation.render_for(Column, model='dropdown')
def render_column_dropdown(self, h, comp, *args):
    """Render the column menu"""
    with h.div(class_="dropdown menu"):
        with h.ul:
            if not self.is_archive:
                with h.li:
                    onclick = (
                        u"if (confirm(%(message)s)){"
                        u" window.location='%(callback)s';"
                        u"}" %
                        {
                            'message': ajax.py2js(
                                _(u'The list will be deleted. Are you sure?')
                            ).decode('UTF-8'),
                            'callback': h.SyncRenderer().a.action(
                                self.actions, 'delete', comp
                            ).get('href')
                        }
                    )
                    h << h.a(_(u'Delete this list'), onclick=onclick)
                if self.cards:
                    with h.li:
                        onclick = (
                            u"if (confirm(%(message)s)){"
                            u" window.location='%(callback)s';"
                            u"}" %
                            {
                                'message': ajax.py2js(
                                    _(u'All the cards will be archived. Are you sure?')
                                ).decode('UTF-8'),
                                'callback': h.SyncRenderer().a.action(
                                    self.actions, 'empty', comp
                                ).get('href')
                            }
                        )
                        h << h.a(_(u'Empty this list'), onclick=onclick)
                h << self.card_counter.render(h, 'menu-entry')
            elif self.cards:
                with h.li:
                    onclick = "if (confirm(%(message)s)){window.location='%(purge_func)s';}" % {
                        'message': ajax.py2js(
                            _(u'All cards will be deleted. Are you sure?')
                        ).decode('UTF-8'),
                        'purge_func': h.SyncRenderer().a.action(
                            self.actions, 'purge', comp
                        ).get('href')
                    }
                    h << h.a(_('Purge the cards'), onclick=onclick)

    return h.root


@presentation.render_for(Column, model='header')
def render_column_header(self, h, comp, *args):
    with h.div(class_='list-header', id=self.id + '_header'):
        h << h.a(class_='hidden', id=self.id + '_refresh').action(ajax.Update())
        with h.div(class_='list-title'):
            with h.div(class_='title'):
                h << self.title.render(h.AsyncRenderer(), 0 if security.has_permissions('edit', self) and not self.is_archive else 'readonly')
        h << self.card_counter.render(h, 'header')
        with h.div(class_='list-actions with-dropdown'):
            if security.has_permissions('edit', self):
                h << h.a(h.i(class_='icon-dot-menu'),
                         href='#', class_="toggle-dropdown",
                         onclick="YAHOO.kansha.app.toggleMenu(this)") << ' '
                h << comp.render(h, 'dropdown')
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
        "  YAHOO.kansha.dnd.initList(%(list_id)s);"
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
        # h << self.card_counter.render(h, 'body')
    kw = {}
    if not security.has_permissions('edit', self):
        kw['style'] = 'width: 0px'
    with h.div(class_='list-footer', id=self.id + '_footer', **kw):
        # This HACK is to force nagare to insert its div, otherwise it breaks all the layout.
        if self.is_archive or not security.has_permissions('edit', self):
            h << {'style': 'display: none'}
        h << h.div(self.new_card.on_answer(self.ui_create_card, comp))

    return h.root


@presentation.render_for(NewColumnEditor)
def render_NewColumnEditor(self, h, comp, *args):
    """Render column creator"""
    h << h.h2(_(u'Add list'))
    with h.form:
        with h.div:
            id_ = h.generate_id()
            h << h.label(_('Name'), for_=id)
            h << h.input(id=id_, type='text', value=self.title(),
                         placeholder=_('List title'),
                         autofocus=True).error(self.title.error).action(self.title)

        with h.div:
            id_ = h.generate_id()
            h << h.label(_('Position'), for_=id_)
            with h.select(id=id_).error(self.index.error).action(self.index):
                for i in xrange(1, self.columns_count + 2):
                    h << h.option(i, value=i - 1).selected(i)

        # FIXME
        with h.div:
            id_ = h.generate_id()
            h << h.label(_('Number max of cards'), id_=id_)
            h << h.input(id=id_, type='text', value=self.nb_cards()).error(self.nb_cards.error).action(self.nb_cards)
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
        visibility = ' hidden'
        if self.column.nb_max_cards:
            visibility = '' if self.check_add() else ' limitReached'
        with h.div(class_='cardCounter' + visibility, id=self.id):
            with h.a().action(comp.call, self, 'edit'):
                h << self.column.count_cards << '/' << (self.column.nb_max_cards or 0)
    h << h.script(
        "YAHOO.kansha.app.saveLimit(%(list_id)s, %(limit)s);"
        "YAHOO.kansha.app.countCards(%(list_id)s);" %
        {
            'list_id': ajax.py2js(self.column.id),
            'limit': ajax.py2js(self.column.nb_max_cards or 0)
        }
    )
    return h.root


@presentation.render_for(CardsCounter, 'header')
def render_CardsCounter_header(self, h, comp, model):
    h << self.editable_counter
    return h.root


@presentation.render_for(CardsCounter, 'menu-entry')
def render_CardsCounter_menu(self, h, comp, model):
    with h.li:
        h << h.a(_(u'Set card limit')).action(self.editable_counter.call, self, 'edit')
    return h.root


@presentation.render_for(CardsCounter, 'body')
def render_CardsCounter_body(self, h, comp, model):
    with h.div(class_='no-drop'):
        h << h.i(class_='icon-blocked huge') << h.br
        h << _(u"This list already holds its maximum amount of cards")
    h << h.script("YAHOO.kansha.app.countCards(%s)" % ajax.py2js(self.column.id))
    return h.root


@presentation.render_for(CardsCounter, 'footer')
def render_CardsCounter_footer(self, h, comp, model):
    h << h.script(
        "YAHOO.kansha.app.countCards(%(list_id)s);" %
        {
            'list_id': ajax.py2js(self.column.id),
        }
    )
    return h.root


@presentation.render_for(CardsCounter, model='edit')
def render_CardsCounter_edit(self, h, comp, *args):
    """Render the title of the associated object"""
    text = var.Var(self.text)
    with h.div(class_='list-counter'):
        with h.div(class_='cardCounter'):
            with h.form(onsubmit='return false;'):
                action = h.input(type='submit').action(lambda: self.validate(text(), comp)).get('onclick')
                id_ = h.generate_id()
                h << h.input(id=id_, type='text', value=self.column.nb_max_cards or '', onblur=action).action(text)
                h << h.script(
                    """YAHOO.util.Event.on(%s, 'keyup', function (e) {
                            if (e.keyCode == 13) {
                                e.preventDefault();
                                this.blur();
                            }
                            var result = this.value.replace(/[^0-9]/g, '')
                            if (this.value !=result) {
                               this.value = result;
                            }
                     });""" % ajax.py2js(id_)
                )
                h << h.script(
                    "YAHOO.kansha.app.selectElement(%s);" % ajax.py2js(id_)
                )
        if self.error is not None:
            with h.div(class_='nagare-error-message'):
                h << self.error
    return h.root
