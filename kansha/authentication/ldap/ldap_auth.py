# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
from nagare import log
try:
    import ldap
except ImportError:
    ldap = None
import sys
import types


def get_class(fullpath):
    mod, classname = fullpath.split(':')
    mod = sys.modules[mod]
    return getattr(mod, classname)


def toUTF8(v):
    if isinstance(v, unicode):
        return v.encode('utf-8')
    elif isinstance(v, (types.TupleType, types.ListType)):
        return [toUTF8(e) for e in v]
    elif isinstance(v, types.DictType):
        return dict([(toUTF8(k), toUTF8(v_)) for k, v_ in v.items()])
    else:
        return v


class LDAPAuth(object):
    def __init__(self, ldap_cfg):
        ldap_cfg = toUTF8(ldap_cfg)
        self.server = "ldap://" + ldap_cfg['server']
        self.users_base_dn = ldap_cfg['users_base_dn']

    def connect(self):
        """Connect to LDAP server

        Return:
            - a server connection
        """
        assert ldap, 'python_ldap not installed'
        return ldap.initialize(self.server)

    def get_user_dn(self, uid):
        raise NotImplementedError()

    def check_password(self, uid, password):
        """Check if the specified couple user/password is correct

        In:
           - ``uid`` -- the user id
           - ``password`` -- the user password
        Return:
            - True if password is checked
        """
        c = self.connect()
        dn = self.get_user_dn(uid)
        # Try to authenticate
        try:
            c.simple_bind_s(dn, password.encode('UTF-8'))
            return True
        except ldap.INVALID_CREDENTIALS:
            log.info("Bad credentials for DN %r" % dn)
        except ldap.SERVER_DOWN:
            log.critical("LDAP server down")
        finally:
            c.unbind()

    def get_profile(self, uid, password):
        raise NotImplementedError()


class NngLDAPAuth(LDAPAuth):
    def get_user_dn(self, uid):
        """Construct a user DN given an user id

        In:
            - ``uid`` -- the user id
        Return:
            - a string, the user DN
        """
        return 'uid=%s,%s' % (ldap.dn.escape_dn_chars(toUTF8(uid)), self.users_base_dn)

    def get_profile(self, uid, password):
        c = self.connect()
        ldap_result = c.search_s(self.get_user_dn(uid), ldap.SCOPE_BASE)[0][1]
        profile = {}
        profile['uid'] = ldap_result['uid'][0]
        profile['name'] = ldap_result['displayName'][0].decode('utf-8')
        profile['email'] = ldap_result['mail'][0]
        profile['picture'] = ldap_result['jpegPhoto'][0] if 'jpegPhoto' in ldap_result else None
        return profile


class ADLDAPAuth(LDAPAuth):
    def connect(self):
        conn = super(ADLDAPAuth, self).connect()
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.protocol_version = 3
        return conn

    def check_password(self, uid, password):
        """Check if the specified couple user/password is correct

        In:
           - ``uid`` -- the user id
           - ``password`` -- the user password
        Return:
            - True if password is checked
        """
        c = self.connect()
        # Try to authenticate
        try:
            c.simple_bind_s(uid, password)
            return True
        except ldap.INVALID_CREDENTIALS:
            log.info("Bad credentials for uid %r" % uid)
        except ldap.SERVER_DOWN:
            log.critical("LDAP server down")
        finally:
            c.unbind()

    def get_profile(self, uid, password):
        c = self.connect()
        c.simple_bind_s(uid, password)
        ldap_result = c.search_s(self.users_base_dn, ldap.SCOPE_SUBTREE, '(userPrincipalName=%s)' % ldap.dn.escape_dn_chars(toUTF8(uid)))[0][1]
        profile = {}
        profile['uid'] = ldap_result['sAMAccountName'][0]
        profile['name'] = ldap_result['displayName'][0].decode('utf-8')
        profile['email'] = ldap_result.get('mail', [''])[0]
        profile['picture'] = ldap_result['thumbnailPhoto'][0] if 'thumbnailPhoto' in ldap_result else None
        c.unbind()
        return profile
