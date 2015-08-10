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


class GoogleConnexion(object):

    source = 'google'

    def __init__(self, google):
        self.google = google


@presentation.render_for(GoogleConnexion)
def render(self, h, comp, *args):
    h << h.a(i18n._('Sign in with Google'), class_="oauth google").action(lambda: comp.call(self.google))
    return h.root


class FacebookConnexion(object):

    source = 'facebook'

    def __init__(self, facebook):
        self.facebook = facebook


@presentation.render_for(FacebookConnexion)
def render(self, h, comp, *args):
    h << h.a(i18n._('Sign in with Facebook'), class_="oauth facebook").action(lambda: comp.call(self.facebook))
    return h.root


class Login(object):

    def __init__(self, oauth_cfg):
        self.oauth_modules = {}
        google_cfg = oauth_cfg['google']
        if google_cfg['activated']:
            self.oauth_modules['google'] = component.Component(
                GoogleConnexion(oauth_providers.Google(google_cfg['key'],
                                                       google_cfg['secret'],
                                                       ['profile', 'email'])))
        facebook_cfg = oauth_cfg['facebook']
        if facebook_cfg['activated']:
            self.oauth_modules['facebook'] = component.Component(
                FacebookConnexion(oauth_providers.Facebook(facebook_cfg['key'],
                                                           facebook_cfg['secret'],
                                                           ['email'])))

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
