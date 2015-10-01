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
def init_app__board(self, url, comp, http_method, request):
    kansha = self.task().app
    kansha.select_board_by_uri(url[1])


@presentation.init_for(App, "url[0] == 'logout'")
def init_app__logout(self, url, comp, http_method, request):
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
def init_app__register(self, url, comp, http_method, request):
    register = self._services(
        forms.RegistrationTask,
        self.app_title,
        self.app_banner,
        self.custom_css,
        self.mail_sender
    )
    register.state = (url[1], url[2])
    comp.becomes(register).on_answer(lambda v: logout())


@presentation.init_for(App, "len(url) == 3 and url[0] == 'new_mail'")
def init_app__new_mail(self, url, comp, http_method, request):
    username, token = (url[1], url[2])
    get_user = lambda: UserManager.get_by_username(username)
    confirmation = self._services(
        forms.EmailConfirmation,
        self.app_title,
        self.app_banner,
        self.custom_css,
        get_user
    )
    if confirmation.confirm_email_address(token):
        log.debug(_('Change email success for user %s') % get_user().username)
        comp.becomes(self._services(
            forms.ChangeEmailConfirmation,
            self.app_title,
            self.app_banner,
            self.custom_css,
            request.application_url
        ),
            model='success'
        )
        confirmation.reset_token(token)
    else:
        log.debug(_('Change email failure for user %s') % get_user().username)
        comp.becomes(
            self._services(
                forms.ChangeEmailConfirmation,
                self.app_title,
                self.app_banner,
                self.custom_css,
                request.application_url
            ),
            model='failure'
        )


@presentation.init_for(App, "len(url) == 3 and url[0] == 'reset'")
def init_app__reset(self, url, comp, http_method, request):
    reset = self._services(
        forms.PasswordResetTask,
        self.app_title,
        self.app_banner,
        self.custom_css,
        self.mail_sender
    )
    reset.state = (url[1], url[2])
    comp.becomes(reset).on_answer(lambda v: logout())


@presentation.init_for(App, "len(url) >= 2 and url[0] == 'assets'")
def init_app__assets(self, url, comp, http_method, request):
    component.Component(self.assets_manager).init(url[1:], http_method, request)
