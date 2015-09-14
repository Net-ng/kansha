# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation, security, log, component
from nagare.i18n import _

from .. import models
from .app import App, WSGIApp
from ..exceptions import NotFound
from ..authentication.database import forms
from ..user.usermanager import UserManager
from ..gallery import comp as gallery, models as gallery_models


def logout():
    if security.get_user() is not None:
        security.get_manager().logout()


@presentation.init_for(App, "len(url) == 2")
def init_static(self, url, comp, http_method, request):
    kansha = self.task().app
    kansha.select_board_by_uri(url[1])


@presentation.init_for(App, "url[0] == 'logout'")
def init_static(self, url, comp, http_method, request):
    logout()


@presentation.init_for(App)
def init_app(self, url, comp, http_method, request):
    """
    Forward everything to the MainTask to maintain compatibility and catch
    404 errors to use custom error page
    """
    log.error('url "%s" not found' % request.url)
    raise NotFound()


@presentation.init_for(App, "len(url) == 3 and url[0] == 'register'")
def init_static(self, url, comp, http_method, request):
    register = forms.RegistrationTask(self.banner, self.custom_css, comp().mail_sender)
    register.state = (url[1], url[2])
    comp.becomes(register).on_answer(lambda v: logout())


@presentation.init_for(App, "len(url) == 3 and url[0] == 'new_mail'")
def init_static(self, url, comp, http_method, request):
    username, token = (url[1], url[2])
    get_user = lambda: UserManager.get_by_username(username)
    confirmation = forms.EmailConfirmation(self.banner, self.custom_css, get_user)
    if confirmation.confirm_email_address(token):
        log.debug(_('Change email success for user %s') % get_user().username)
        comp.becomes(forms.ChangeEmailConfirmation(self.banner, self.custom_css, request. application_url), model='success')
        confirmation.reset_token(token)
    else:
        log.debug(_('Change email failure for user %s') % get_user().username)
        comp.becomes(forms.ChangeEmailConfirmation(self.banner, self.custom_css, request.application_url), model='failure')


@presentation.init_for(App, "len(url) == 3 and url[0] == 'reset'")
def init_static(self, url, comp, http_method, request):
    reset = forms.PasswordResetTask(self.banner, self.custom_css, comp().mail_sender)
    reset.state = (url[1], url[2])
    comp.becomes(reset).on_answer(lambda v: logout())


@presentation.init_for(App, "len(url) >= 2 and url[0] == 'assets'")
def init_assets(self, url, comp, http_method, request):
    component.Component(self.assets_manager).init(url[1:], http_method, request)
