# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import peak.rules

from nagare import presentation
from nagare.i18n import _
from kansha.user import comp, user_profile, usermanager


class GoogleUser(comp.User):

    def __init__(self, username, *args, **kw):
        """Initialization

        In:
            - ``username`` -- the id of the user
        """
        super(comp.User, self).__init__(username, 'passwd')
        self.username = username
        self._data = kw.get('data')


@peak.rules.when(usermanager.get_user_class, """source != 'application'""")
def get_user_class(source):
    return GoogleUser


class GoogleUserForm(user_profile.BasicUserForm):
    pass
