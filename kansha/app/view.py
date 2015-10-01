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
from nagare import ajax, component, presentation, security
from nagare.i18n import _

from kansha import VERSION
from ..user.usermanager import get_app_user
from ..user import user_profile
from .app import Kansha, App

from ..services.dummyassetsmanager.dummyassetsmanager import DummyAssetsManager


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
            self.custom_css,
            user.data,
            self.mail_sender, 
            self.assets_manager,
            self.search_engine
        )
        self.content.becomes(u, 'edit')


@presentation.render_for(Kansha, model='menu')
def render(self, h, comp, *args):
    """Main menu part"""
    kw = {'onclick': "YAHOO.kansha.app.toggleMenu('mainNavbar')"}
    with h.div(class_='navbar', id='mainNavbar'):
        with h.div(class_='navActions', id='mainActions'):
            # If login, display logout button
            user = security.get_user()
            if user:
                # User menu
                self.user_menu.on_answer(lambda v: answer_on_menu(self, comp, user, v))
                h << self.user_menu.render(h, 'menu')
            else:
                with h.div(id='login'):
                    h << h.a("login", href=h.request.application_url)

        # Tab part
        with h.div(class_="tab collapse", **kw):
            h << self.title.render(h.AsyncRenderer())
    return h.root


@presentation.render_for(Kansha, model='tab')
def render(self, h, comp, *args):
    user = security.get_user()
    if user is None:
        h << h.a(self.app_title, class_="collapse", id="mainTab")
    else:
        app_user = get_app_user(user.username)
        h << h.a(component.Component(app_user, "avatar"), self.app_title, id="mainTab")
    return h.root


@presentation.render_for(Kansha, model='yui-deps')
def render(self, h, comp, *args):
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
def render(self, h, comp, *args):
    """Main renderer"""
    h << comp.render(h, model='yui-deps')

    h.head << h.head.meta(
        name='viewport', content='width=device-width, initial-scale=1.0')

    h.head.css_url('css/bootstrap.min.css')
    h.head.css_url('css/responsive-kansha.css')
    if self.custom_css:
        h.head.css_url(self.custom_css)
    h.head.css_url('css/fonts.css')

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
                        h << self.content
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
                h << self.content

    h << h.script(src=h.head.static_url + 'js/nagare.js', type='text/javascript')

    return h.root


@presentation.render_for(App, model="debug")
def render(self, h, comp, *args):
    h.head.css_url(
        ajax.YUI_INTERNAL_PREFIX + '/logger/assets/skins/sam/logger.css')
    h.head.javascript_url(ajax.YUI_INTERNAL_PREFIX + '/logger/logger-min.js')
    h << h.script('var myLogReader = new YAHOO.widget.LogReader("myLogger");')
    h << h.div(id="myLogger")
    return h.root


@presentation.render_for(App)
def render(self, h, comp, *args):
    favicon_url = h.head.static_url + "img/favicon.ico"
    h.head << h.head.link(rel="icon", type="image/x-icon", href=favicon_url)
    h.head << h.head.link(rel="shortcut icon", type="image/x-icon", href=favicon_url)

    h << self.task
    if False:
        h << comp.render(h, "debug")
    return h.root
