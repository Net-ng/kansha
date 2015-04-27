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


@presentation.render_for(GoogleUserForm, model="edit")
def render(self, h, comp, *args):
    with h.div(class_='row-fluid span8'):
        with h.form:
            with h.ul(class_='unstyled'):
                with h.li:
                    h << _('Fullname')
                    h << h.input(disabled=True, value=self.fullname())
                with h.li:
                    h << _('Email')
                    h << h.input(disabled=True, value=self.email())
                with h.li:
                    h << _('Language')
                    with h.select().action(self.language).error(self.language.error):
                        for (id, lang) in user_profile.LANGUAGES.items():
                            if self.language() == id:
                                h << h.option(lang, value=id, selected='')
                            else:
                                h << h.option(lang, value=id)
                if self.target.picture:
                    with h.li:
                        h << _('Picture')
                        h << h.div(
                            h.img(src=self.target.picture, class_="avatar big"))

            with h.div:
                h << h.input(value=_("Save"), class_="btn btn-primary btn-small",
                             type='submit').action(self.commit)
    return h.root


@peak.rules.when(user_profile.get_userform, """source == 'ldap'""")
@peak.rules.when(user_profile.get_userform, """source == 'facebook'""")
@peak.rules.when(user_profile.get_userform, """source == 'google'""")
def get_userform(app_title, custom_css, source):
    """ User form for application user
    """
    return GoogleUserForm
