# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import datetime

from nagare.i18n import _
from nagare.namespaces.xhtml import absolute_url
from nagare import ajax, component, presentation, security

from kansha import VERSION
from kansha.user.usermanager import UserManager

from .comp import Kansha


def answer_on_menu(self, comp, user, v):
    """
    In:
        - ``self`` -- Kansha application
        - ``comp`` -- Component wrapped application
        - ``user`` -- current user
        - ``v`` -- value returned
    """
    if v is None:
        comp.answer(None)
    else:
        self._on_menu_entry('boards')


@presentation.render_for(Kansha, model='menu')
def render_kansha_menu(self, h, comp, *args):
    """Main menu part"""
    with h.div(class_='nav-menu', onclick='YAHOO.kansha.app.toggleMainMenu(this)'):
        with h.ul(class_='actions'):
            # If login, display logout button
            user = security.get_user()
            if user:
                # User menu
                self.user_menu.on_answer(lambda v: answer_on_menu(self, comp, user, v))
                h << self.user_menu.render(h, 'menu')
            else:
                h << h.li(h.a(_(u"Login"), href=h.request.application_url))

        # Tab part
        h << h.span(self.title.render(h.AsyncRenderer()), class_="menu-title", id='kansha-nav-menu')
    return h.root


@presentation.render_for(Kansha, model='tab')
def render_kansha_tab(self, h, comp, *args):
    user = security.get_user()
    if user is None:
        h << h.a(self.app_title)
    else:
        app_user = UserManager.get_app_user(user.username)
        h << h.a(component.Component(app_user, "avatar"), self.app_title)
    return h.root


@presentation.render_for(Kansha, model='yui-deps')
def render_kansha_yui_deps(self, h, comp, *args):
    """YUI CSS and JS dependencies"""
    for e in ('container', 'colorpicker', 'autocomplete', 'resize', 'imagecropper'):
        h.head.css_url(ajax.YUI_INTERNAL_PREFIX +
                       '/%(module)s/assets/skins'
                       '/sam/%(module)s.css' % dict(module=e))

    h.head.javascript_url(
        ajax.YUI_INTERNAL_PREFIX + '/yahoo-dom-event/yahoo-dom-event.js')
    minified = ('connection', 'animation', 'dragdrop', 'element', 'get',
                'json', 'container', 'slider', 'colorpicker', 'datasource',
                'autocomplete', 'selector', 'resize', 'imagecropper', 'selector')
    for e in minified:
        h.head.javascript_url(ajax.YUI_INTERNAL_PREFIX +
                              '/%(module)s/%(module)s-min.js' % dict(module=e))
    return h.root


@presentation.render_for(Kansha, model='resync')
def render_Kansha_resync(self, h, comp, model):
    with h.div(id="resync", style='display:none'):
            h << h.a(_(u'click here to resync'), id='resync-action').action(self.initialization)
    return h.root


@presentation.render_for(Kansha, model='oip')
def render_Kansha_oip(self, h, comp, model):
    with h.div(id="oip", style='display:none'):
        h << h.h2(_(u'Operation in progress'), class_='title')
        with h.div(class_='content'):
            h << h.p(h.img(src='img/ajax-loader.gif'), u' ', _(u'Please wait until operation completes.'))
    return h.root


@presentation.render_for(Kansha, 'home_menu')
def render_user_profile__menu(self, h, comp, *args):
    with h.div(class_='menu'):
        with h.ul:
            for id_, entry in self.home_menu.iteritems():
                with h.li:
                    with h.a.action(self._on_menu_entry, id_):
                        h << h.i(class_='icon icon-' + entry.icon)
                        h << h.span(entry.label)
                        if self.selected == id_:
                            h << {'class': 'active'}
    return h.root


@presentation.render_for(Kansha)
def render_kansha(self, h, comp, *args):
    """Main renderer"""

    favicon_url = absolute_url(self.favicon, h.head.static_url)
    h.head << h.head.link(rel="icon", type="image/x-icon", href=favicon_url)
    h.head << h.head.link(rel="shortcut icon", type="image/x-icon", href=favicon_url)

    h << comp.render(h, model='yui-deps')

    h.head << h.head.meta(
        name='viewport', content='width=device-width, initial-scale=1.0')

    h.head.css_url('css/knacss.css')
    h.head.css_url('css/themes/fonts.css?v=2c')
    h.head.css_url('css/themes/kansha.css?v=2c')
    h.head.css_url('css/themes/%s/kansha.css?v=2c' % self.theme)

    h.head.javascript_url('js/jquery-2.1.3.min.js')
    h.head.javascript_url('js/jquery-ui-1.11.2.custom/jquery-ui.js')

    h.head.javascript_url("js/jquery-linkify/jquery.linkify.min.js")

    h.head.javascript_url('js/dnd.js?v=2d')
    h.head.javascript_url('js/kansha.js?v=2c')
    h.head.javascript_url('js/autocomplete.js')

    h.head.javascript_url('js/wysihtml/dist/minified/wysihtml.min.js?v=2c')
    h.head.javascript_url('js/wysihtml/dist/minified/wysihtml.toolbar.min.js?v=2c')
    h.head.javascript_url('js/wysihtml/parser_rules/simple.js')

    if self.selected == 'board':
        with h.body(class_='yui-skin-sam'):
            h << h.div(id="mask")
            h << comp.render(h, model='resync')
            h << comp.render(h, model='oip')
            with h.div(id='application'):
                h << comp.render(h, model='menu')
                h << self.content.on_answer(self.handle_event)
    else:
        h.head << h.head.title(self.app_title)
        with h.body(class_='yui-skin-sam'):
            with h.div(class_='wrap'):
                with h.div(class_='container'):
                    h << h.div(id="mask")
                    h << comp.render(h, model='resync')
                    h << comp.render(h, model='oip')
                    with h.div(id='application'):
                        h << comp.render(h, model='menu')

                        with h.div(class_='home'), h.div(class_='grid-2'):
                            h << comp.render(h, 'home_menu')
                            with h.div(class_='boards'):
                                # answer only happens when a new board is created
                                h << self.content.on_answer(self.select_board).render(h.AsyncRenderer())
            with h.div(class_='credits'):
                with h.div(class_='container'):
                    h << h.a(self.app_title, href='http://www.kansha.org', target='_blank') << (u' v%s - \u00a9 ' % VERSION)
                    h << h.a('Net-ng', href='http://www.net-ng.com', target='_blank') << (' %d' % datetime.date.today().year)

    h.head.javascript_url('js/nagare.js')

    return h.root
