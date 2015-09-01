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
from . import oauth_providers


class OAuthConnection(object):

    def __init__(self, provider):

        self.provider = provider

    @property
    def source(self):
        return self.provider.name


@presentation.render_for(OAuthConnection)
def render_button(self, h, comp, *args):
    h << h.a(
        i18n._('Sign in with %s') % self.source.capitalize(),
        class_="oauth " + self.source
    ).action(lambda: comp.call(self.provider))
    return h.root


class Login(object):

    def __init__(self, oauth_cfg):
        self.oauth_modules = {}

        for source, cfg in oauth_cfg.iteritems():
            try:
                if cfg['activated']:
                    self.oauth_modules[source] = component.Component(
                        OAuthConnection(
                            oauth_providers.providers[source](
                                cfg['key'],
                                cfg['secret'],
                                ['profile', 'email']
                            )
                        )
                    )
            except TypeError:
                # source is not a provider entry
                continue

    def connect(self, oauth_user, source):
        if oauth_user is None:
            u = None
        else:
            profile = oauth_user.get_profile()[0]
            data_user = usermanager.UserManager.get_by_username(profile['id'])
            # if user exists update data
            if not data_user:
                u = profile
                data_user = usermanager.UserManager().create_user(profile['id'], None,
                                                                  profile.get('name'),
                                                                  profile['email'],
                                                                  source=source,
                                                                  picture=profile.get('picture'))
            data_user.update(profile.get('name'), profile['email'],
                             picture=profile.get('picture'))
            database.session.flush()
            u = usermanager.get_app_user(profile['id'], data=data_user)
            security.set_user(u)
        return u


@presentation.render_for(Login)
def render(self, h, comp, *args):
    with h.div(class_="oauthLogin"):
        for (source, oauth) in self.oauth_modules.items():
            h << oauth.on_answer(lambda u, source=source: comp.answer(self.connect(u, source)))
    return h.root
