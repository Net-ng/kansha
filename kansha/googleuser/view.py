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
from kansha.user import comp, user_profile
from comp import GoogleUser, GoogleUserForm


@peak.rules.when(user_profile.get_userform, """source != 'application'""")
def get_userform(app_title, app_banner, custom_css, source):
    """ User form for application user
    """
    return GoogleUserForm
