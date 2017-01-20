# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation, var, database, security
from nagare.i18n import _
from nagare.admin.reference import load_object

from ...user import usermanager
from kansha.services.authentication_repository import Authentication


class Login(Authentication):

    alt_title = None

    CONFIG_SPEC = {
        'activated': 'boolean(default=False)',
        'host': 'string(default="localhost")',
        'port': 'integer(default=389)',
        'users_base_dn': 'string(default="")',
        'schema': 'string(default="kansha.authentication.ldap.ldap_auth:NngLDAPAuth")'
    }

    def __init__(self, app_title, app_banner, theme, assets_manager_service):
        cls = load_object(self.config['schema'])[0]
        self.ldap_engine = cls(self.config)
        self.error_message = ''
        self.assets_manager = assets_manager_service

    def connect(self, uid, passwd, comp):
        if (uid != '' and passwd != '' and
                self.ldap_engine.check_password(uid, passwd)):
            data_user = usermanager.UserManager.get_by_username(uid)
            profile = self.ldap_engine.get_profile(uid, passwd)
            # if user exists update data
            if profile['picture']:
                self.assets_manager.save(profile['picture'], uid,
                                         {'filename': uid})
                picture = self.assets_manager.get_image_url(uid, 'thumb')
            else:
                picture = None
            if not data_user:
                data_user = usermanager.UserManager().create_user(uid, None,
                                                                  profile['name'], profile['email'], source='ldap',
                                                                  picture=picture)
            data_user.update(profile['name'], profile['email'],
                             picture=picture)
            database.session.flush()
            u = usermanager.UserManager.get_app_user(uid, data=data_user)
            security.set_user(u)
            comp.answer(u)
        else:
            self.error_message = _('Login failed')


@presentation.render_for(Login)
def render(self, h, comp, *args):
    with h.div(class_='login LDAPLogin'):
        with h.form:
            # if self.error_message:
            #     h << h.br << h.div(self.error_message, class_="error")
            uid = var.Var()
            h << h.input(type='text', name='__ac_name',
                         id='ldap_username', placeholder=_('Enter username')).action(uid)
            passwd = var.Var()
            h << h.input(
                type='password', name='__ac_password',
                id='ldap_password', placeholder=_('Enter password')).action(passwd)
            with h.div(class_='actions'):
                h << h.input(type='submit', value=_(u'Sign in with LDAP'),
                             class_='btn btn-primary'
                             ).action(lambda: self.connect(uid(), passwd(), comp))

    return h.root
