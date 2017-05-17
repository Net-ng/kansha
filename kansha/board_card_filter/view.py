# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from nagare.i18n import _, _N, _L
from nagare import ajax, component, presentation, security, var

from .comp import BoardCardFilter


@presentation.render_for(BoardCardFilter, 'search_results')
def render_search_results(self, h, comp, *args):
    h << h.script('YAHOO.kansha.app.highlight_cards(%s);' % ajax.py2js(list(self.card_matches), h))
    h << comp.render(h, 'num_matches')
    self._changed = False
    return h.root


@presentation.render_for(BoardCardFilter, 'footer')
def render_search_results(self, h, comp, *args):
    if self._changed:
        h << comp.render(h, 'search_results')
        h << h.script('$("#search input").val("");')
    return h.root


@presentation.render_for(BoardCardFilter)
@presentation.render_for(BoardCardFilter, 'num_matches')
def render_num_matches(self, h, comp, *args):
    local_h = h.SyncRenderer()
    input_class = ''
    if self.card_matches:
        if None in self.card_matches:
            local_h << local_h.span(_(u'No matches'), class_='nomatches')
            input_class = 'nomatches'
        else:
            n = len(self.card_matches)
            local_h << (_N(u'%d match', u'%d matches', n) % n)
            input_class = 'highlight'
    else:
        local_h << u' '
    res = (local_h.root if isinstance(local_h.root, basestring) else
           local_h.root.write_htmlstring())
    h << h.script(u'$("#show_results").html(%s);' % ajax.py2js(res).decode('utf-8'))
    h << h.script('document.getElementById("search").className = "%s";' % input_class)
    return h.root


@presentation.render_for(BoardCardFilter, 'search_input')
def render_num_matches(self, h, comp, *args):
    h.head.javascript_url('js/debounce.js')
    h.head.javascript_url('js/search.js?v=2c')

    search_cb = h.input.action(ajax.Update(
        action=self.search,
        component_to_update='show_results',
        render=lambda renderer: comp.render(renderer, 'search_results')
    )).get('onchange').replace('this', 'elt')
    oninput = 'debounce(this, function(elt) { %s; }, 500)' % search_cb
    h << h.div(id_='show_results')
    if self.card_matches:
        if None in self.card_matches:
            klass = 'nomatches'
        else:
            klass = 'highlight'
    else:
        klass = ''
    with h.div(id='search', class_=klass):
        h << h.input(type='text', placeholder=_(u'search'),
                     value=self.last_search,
                     oninput=oninput)
        with h.span(class_='icon'):
            h << h.i(class_='icon-search search_icon',
                     style='display:none' if self.last_search else '')
            h << h.a(h.i(class_='icon-cancel-circle'), href='#', class_='search_close',
                     style='' if self.last_search else 'display: none')
    h << comp.render(h, 'num_matches')

    return h.root
