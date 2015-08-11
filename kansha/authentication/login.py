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

    def __init__(self, app_title, custom_css):
        self.app_title = app_title
        self.custom_css = custom_css


@presentation.render_for(Header)
def render_Header(self, h, comp, *args):
    """Head renderer"""

    h.head << h.head.title(self.app_title)
    h.head << h.head.meta(
        name='viewport', content='width=device-width, initial-scale=1.0')

    h.head.css_url('css/knacss.css')
    h.head.css_url('css/login.css')
    if self.custom_css:
        h.head.css_url(self.custom_css)

    with h.div(class_='header'):
        h << h.div(class_='logo')
        h << h.h1(self.app_title)
    return h.root


class Credits(object):

    def __init__(self, app_title, custom_css):
        self.app_title = app_title
        self.header = component.Component(Header(self.app_title, custom_css))


@presentation.render_for(Credits)
def render_Credits(self, h, comp, model):
    h << self.header
    with h.div(class_='credits-content'):
        with h.ol:
            with h.li:
                h << h.span(u'One')
                h << h.p(u'''Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam pharetra dolor vitae neque ullamcorper accumsan id id risus. Aliquam tempus libero tempor, varius tortor vel, congue diam. Aenean enim enim, bibendum in libero ac, hendrerit ultricies nunc. Sed placerat ante nec ligula viverra rhoncus. In vitae quam condimentum, dapibus augue et, blandit nulla. Phasellus fringilla placerat nisl, non porta tortor semper vitae. Proin lectus lorem, pretium id vulputate a, scelerisque non nisl. Pellentesque lorem ante, blandit eget fermentum id, aliquam sed justo. Quisque at massa a neque imperdiet ornare eu eu diam. Donec sed molestie velit. Donec adipiscing ullamcorper aliquam. Nulla euismod erat ut egestas malesuada. Aenean quis justo pellentesque, pulvinar justo id, fermentum libero. Donec sit amet est ut lorem ullamcorper condimentum.''')
            with h.li:
                h << h.span(u'Two')
                h << h.p(u'''Pellentesque urna tortor, dignissim vel ligula quis, varius volutpat turpis. Suspendisse varius non massa vel imperdiet. Cras eget justo dictum, eleifend urna ut, facilisis nisi. Donec at dolor eu arcu sodales rhoncus eget vitae augue. Mauris quam dui, varius a enim in, hendrerit luctus leo. Morbi purus dolor, ullamcorper vel ante egestas, luctus condimentum magna. Praesent lobortis lacus ut auctor pulvinar.''')
            with h.li:
                h << h.span(u'Three')
                h << h.p(u'''Aenean in ultricies justo. Mauris pulvinar, leo at auctor iaculis, tortor eros iaculis ante, eget tempus nisi nisl sed enim. Mauris ullamcorper ipsum arcu, sed commodo nisl vestibulum posuere. Proin semper neque quis suscipit condimentum. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Sed est felis, viverra in nulla eget, posuere dignissim lectus. Etiam neque sem, pellentesque non dignissim vitae, suscipit pretium leo. Sed pharetra non dolor ut tempus. Sed vehicula orci quis laoreet cursus.''')
            with h.li:
                h << h.span(u'Four')
                h << h.p(u'''Donec nec arcu tortor. Interdum et malesuada fames ac ante ipsum primis in faucibus. Donec nunc eros, convallis ut lectus nec, gravida ultrices dui. Vestibulum malesuada ornare nisi. Nunc convallis velit erat, sit amet tempor tellus tempor eget. Integer volutpat, neque nec convallis tempus, libero metus cursus nulla, et aliquet nulla mi eu dolor. Morbi ante tortor, fringilla quis vestibulum nec, luctus eu sem.''')
            with h.li:
                h << h.span(u'Five')
                h << h.p(u'''Pellentesque velit arcu, congue et congue bibendum, varius in risus. Suspendisse egestas tincidunt elit nec laoreet. Morbi molestie risus sollicitudin tristique luctus. Morbi sed massa quis mauris convallis lacinia eu ut massa. Integer at nulla ac metus sollicitudin bibendum. Aliquam erat volutpat. Duis eget erat elementum, varius odio et, rhoncus dui. Vestibulum porta eget magna sit amet auctor. Integer ultricies elit ut vestibulum consequat. Fusce quis quam malesuada, interdum leo eu, posuere nibh. Phasellus pulvinar augue nec urna dapibus porttitor. Etiam metus diam, porttitor eu justo bibendum, imperdiet suscipit nibh. ''')
        with h.p:
            h << h.a(_(u'Back')).action(comp.answer)
    return h.root


class Login(object):

    def __init__(self, app_title, custom_css, mail_sender, auth_cfg, assets_manager):
        """Login components

        """
        logins = []
        if auth_cfg['dbauth']['activated']:
            logins.append(database_form.Login(app_title, custom_css, mail_sender, auth_cfg['dbauth']))
        if auth_cfg['oauth']['activated']:
            logins.append(oauth.Login(auth_cfg['oauth']))
        if auth_cfg['ldapauth']['activated']:
            logins.append(ldap.Login(auth_cfg['ldapauth'], assets_manager))

        self.app_title = app_title
        self.logins = [component.Component(login) for login in logins]
        self.header = component.Component(Header(self.app_title, custom_css))
        self.disclaimer = auth_cfg['disclaimer']


@presentation.render_for(Login)
def render_Login(self, h, comp, *args):
    with h.body(class_='body-login'):
        h << self.header
        with h.div(class_='title'):
            h << h.h2(_(u'Sign in'))
            for login in self.logins:
                if getattr(login(), 'error_message', u''):
                    h << h.small(login().error_message, class_='error')
        with h.div(class_='container'):
            for index, login in enumerate(self.logins, 1):
                h << login.on_answer(comp.answer)

        with h.div(class_='message'):
            h << h.parse_htmlstring(self.disclaimer) if self.disclaimer else u''
        with h.div(class_='credits'):
            h << h.span(u'%s v%s - \u00a9 Net-ng %d' % (self.app_title, VERSION, datetime.date.today().year))

    return h.root
