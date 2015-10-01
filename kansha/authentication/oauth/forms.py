# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation, component, database, security, i18n
from ...user import usermanager
from ..database.forms import RegistrationTask
from . import oauth_providers


class OAuthConnection(object):

    def __init__(self, provider):

        self.provider = provider
        self.content = component.Component()  # workaround nagare weird behavior of call if on_answer registered on this component

    @property
    def source(self):
        return self.provider.name

    def trigger_provider(self, comp):
        r = self.content.call(self.provider)  # here is the trick
        comp.answer(r)


@presentation.render_for(OAuthConnection)
def render_connect(self, h, comp, *args):
    if self.content() is not None:
        return self.content
    else:
        return comp.render(h, 'button')

@presentation.render_for(OAuthConnection, 'button')
def render_button(self, h, comp, *args):
    h << h.a(
        i18n._('Sign in with %s') % self.source.capitalize(),
        class_="oauth " + self.source
    ).action(self.trigger_provider, comp)
    return h.root


SCOPES = {
    'google': ('profile', 'email'),
    'facebook':  ('public_profile', 'email'),
    'twitter': ('profile', 'email'),
    'github': ('user:email',)
}


class Login(object):

    alt_title = None

    def __init__(self, app_title, app_banner, custom_css, mail_sender, oauth_cfg):
        self.oauth_modules = {}
        self._error_message = u''
        self.app_title = app_title
        self.app_banner = app_banner
        self.custom_css = custom_css
        self.mail_sender = mail_sender
        self.oauth_cfg = oauth_cfg
        self.content = component.Component()  # workaround nagare weird behavior of call if on_answer registered on this component

        for source, cfg in oauth_cfg.iteritems():
            try:
                if cfg['activated']:
                    self.oauth_modules[source] = component.Component(
                        OAuthConnection(
                            oauth_providers.providers[source](
                                cfg['key'],
                                cfg['secret'],
                                SCOPES.get(source, ('profile', 'email'))
                            )
                        )
                    )
            except TypeError:
                # source is not a provider entry
                continue

    @property
    def error_message(self):
        return self._error_message or getattr(self.content(), 'error_message', u'')

    @error_message.setter
    def error_message(self, value):
        self._error_message = value
        if self.content():
            setattr(self.content(), 'error_message', u'')

    def connect(self, comp, oauth_user, source):
        if oauth_user is None:
            self._error_message = i18n._(u'Authentication failed')
            return

        profile = oauth_user.get_profile()[0]

        profile_id = profile['id']
        # if user exists update data
        name = profile['name'] or (i18n._(u'Please provide a full name in %s') % source)
        if not usermanager.UserManager.get_by_username(profile_id):
            usermanager.UserManager().create_user(profile['id'], None, name, profile['email'], source=source,
                                                  picture=profile.get('picture'))

        # update takes care of not overwriting the existing email with an empty one
        usermanager.UserManager.get_by_username(profile_id).update(name, profile['email'],
                                                                   picture=profile.get('picture'))
        # thus if data_user.email is empty, that means it has always been so.
        if not usermanager.UserManager.get_by_username(profile_id).email:
            self.content.call(
                RegistrationTask(
                    self.app_title,
                    self.app_banner,
                    self.custom_css,
                    self.mail_sender,
                    '',
                    profile_id
                )
            )
            return
        database.session.flush()
        u = usermanager.get_app_user(profile['id'], data=usermanager.UserManager.get_by_username(profile_id))
        security.set_user(u)

        # After a successful OAuth authentication, we need to manually switch to the user's locale
        # so the first rendering phase uses the correct language
        i18n.set_locale(u.get_locale())

        comp.answer(u)

@presentation.render_for(Login)
def render_login(self, h, comp, *args):

    if self.content() is not None:
        return self.content
    else:
        return comp.render(h, 'buttons')


@presentation.render_for(Login, 'buttons')
def render_buttons(self, h, comp, *args):
    with h.div(class_="oauthLogin"):
        for (source, oauth) in self.oauth_modules.items():
            h << oauth.on_answer(lambda u, source=source: self.connect(comp, u, source))
    return h.root
