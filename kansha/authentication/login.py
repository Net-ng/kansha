# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import datetime

from nagare import presentation, component
from nagare.i18n import _

from kansha import VERSION
from .database import forms as database_form
from .oauth import forms as oauth
from .ldap import forms as ldap


class Header(object):

    def __init__(self, banner, custom_css):
        self.banner = banner
        self.custom_css = custom_css


@presentation.render_for(Header)
def render_Header(self, h, comp, *args):
    """Head renderer"""

    h.head << h.head.title(self.banner)
    h.head << h.head.meta(
        name='viewport', content='width=device-width, initial-scale=1.0')

    h.head.css_url('css/knacss.css')
    h.head.css_url('css/login.css')
    if self.custom_css:
        h.head.css_url(self.custom_css)

    with h.div(class_='header'):
        with h.a(href=h.request.application_url):
            h << h.div(class_='logo')
        h << h.h1(self.banner)
    return h.root


class Login(object):

    def __init__(self, app_title, app_banner, custom_css, mail_sender, cfg, assets_manager):
        """Login components

        """
        logins = []
        auth_cfg = cfg['auth_cfg']
        if auth_cfg['dbauth']['activated']:
            logins.append(database_form.Login(app_title, app_banner, custom_css, mail_sender, auth_cfg['dbauth']))
        if auth_cfg['oauth']['activated']:
            logins.append(oauth.Login(app_title, app_banner, custom_css, mail_sender, auth_cfg['oauth']))
        if auth_cfg['ldapauth']['activated']:
            logins.append(ldap.Login(auth_cfg['ldapauth'], assets_manager))

        self.app_title = app_title
        self.logins = [component.Component(login) for login in logins]
        self.header = component.Component(
            Header(
                cfg['pub_cfg']['banner'],
                custom_css
            )
        )
        self.disclaimer = cfg['pub_cfg']['disclaimer']


@presentation.render_for(Login)
def render_Login(self, h, comp, *args):
    with h.body(class_='body-login slots%s' % len(self.logins)):
        h << self.header
        with h.div(class_='title'):
            title = _(u'Sign in')
            for login in self.logins:
                if login().alt_title:
                    title = login().alt_title
                    break
            h << h.h2(title)
            for login in self.logins:
                if login().error_message:
                    h << h.small(login().error_message, class_='error')
                    login().error_message = u''
        with h.div(class_='container'):
            for index, login in enumerate(self.logins, 1):
                h << login.on_answer(comp.answer)

        with h.div(class_='message'):
            h << h.parse_htmlstring(self.disclaimer) if self.disclaimer else u''
        with h.div(class_='credits'):
            h << h.span(u'%s v%s - \u00a9 Net-ng %d' % (self.app_title, VERSION, datetime.date.today().year))

    return h.root
