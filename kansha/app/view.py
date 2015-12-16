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
from kansha.user import user_profile
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
        u = self._services(
            user_profile.UserProfile,
            self.app_title,
            self.app_banner,
            self.theme,
            self.card_extensions,
            user.data,
            self.search_engine
        )
        self.content.becomes(u, 'edit')


@presentation.render_for(Kansha, model='menu')
def render_kansha_menu(self, h, comp, *args):
    """Main menu part"""
    with h.div(class_='nav-menu'):
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
        h << h.span(self.title.render(h.AsyncRenderer()), class_="title", id='kansha-nav-menu')
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
        h << h.h2(_(u'Synchronization error'), class_='title')
        with h.div(class_='content'):
            link = h.a(_(u'click here to resync'), id='resync-action').action(self.initialization)
            h << h.p(_(u'Your board is out of sync, please '), link, '.')
    return h.root


@presentation.render_for(Kansha, model='oip')
def render_Kansha_oip(self, h, comp, model):
    with h.div(id="oip", style='display:none'):
        h << h.h2(_(u'Operation in progress'), class_='title')
        with h.div(class_='content'):
            h << h.p(h.img(src='img/ajax-loader.gif'), u' ', _(u'Please wait until operation completes.'))
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
    h.head.css_url('css/themes/fonts.css')
    h.head.css_url('css/themes/kansha.css')
    h.head.css_url('css/themes/%s/kansha.css' % self.theme)

    h.head.javascript_url('js/jquery-2.1.3.min.js')
    h.head.javascript_url('js/jquery-ui-1.11.2.custom/jquery-ui.js')

    h.head.javascript_url("js/jquery-linkify/jquery.linkify.min.js")

    h.head.javascript_url('js/dnd.js')
    h.head.javascript_url('js/kansha.js')
    h.head.javascript_url('js/autocomplete.js')

    h.head.javascript_url('js/ckeditor-4.5.3/ckeditor.js')

    if isinstance(self.content(), user_profile.UserProfile):
        with h.body(class_='yui-skin-sam'):
            with h.div(class_='wrap'):
                with h.div(class_='container'):
                    h << h.div(id="mask")
                    h << comp.render(h, model='resync')
                    h << comp.render(h, model='oip')
                    with h.div(id='application'):
                        h << comp.render(h, model='menu')
                        h << self.content.on_answer(self.select_board)
            with h.div(class_='credits'):
                with h.div(class_='container'):
                    h << h.span(u'%s v%s - \u00a9 Net-ng %d' % (self.app_title, VERSION, datetime.date.today().year))
    else:
        with h.body(class_='yui-skin-sam'):
            h << h.div(id="mask")
            h << comp.render(h, model='resync')
            h << comp.render(h, model='oip')
            with h.div(id='application'):
                h << comp.render(h, model='menu')
                h << self.content.on_answer(self.handle_event)

    h.head.javascript_url('js/nagare.js')

    return h.root
