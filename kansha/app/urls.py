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

from kansha.exceptions import NotFound
from kansha.authentication.database import forms
from kansha.user.usermanager import UserManager

from .comp import MainTask


def logout():
    if security.get_user() is not None:
        security.get_manager().logout()


@presentation.init_for(MainTask, "len(url) == 2")
def init_app__board(self, url, comp, http_method, request):
    kansha = self.app
    kansha.select_board_by_uri(url[1])


@presentation.init_for(MainTask, "url[0] == 'logout'")
def init_app__logout(self, url, comp, http_method, request):
    logout()


@presentation.init_for(MainTask)
def init_app(self, url, comp, http_method, request):
    """
    Forward everything to the MainTask to maintain compatibility and catch
    404 errors to use custom error page
    """
    log.error('url "%s" not found' % request.url)
    raise NotFound()


@presentation.init_for(MainTask, "len(url) == 3 and url[0] == 'register'")
def init_app__register(self, url, comp, http_method, request):
    register = self._services(
        forms.RegistrationTask,
        self.app_title,
        self.app_banner,
        self.theme
    )
    register.state = (url[1], url[2])
    comp.becomes(register).on_answer(lambda v: logout())


@presentation.init_for(MainTask, "len(url) == 3 and url[0] == 'new_mail'")
def init_app__new_mail(self, url, comp, http_method, request):
    username, token = (url[1], url[2])
    get_user = lambda: UserManager.get_by_username(username)
    confirmation = self._services(
        forms.EmailConfirmation,
        self.app_title,
        self.app_banner,
        self.theme,
        get_user
    )
    if confirmation.confirm_email_address(token):
        log.debug(_('Change email success for user %s') % get_user().username)
        comp.becomes(self._services(
            forms.ChangeEmailConfirmation,
            self.app_title,
            self.app_banner,
            self.theme,
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
                self.theme,
                request.application_url
            ),
            model='failure'
        )


@presentation.init_for(MainTask, "len(url) == 3 and url[0] == 'reset'")
def init_app__reset(self, url, comp, http_method, request):
    reset = self._services(
        forms.PasswordResetTask,
        self.app_title,
        self.app_banner,
        self.theme,
    )
    reset.state = (url[1], url[2], request.application_url)
    comp.becomes(reset).on_answer(lambda v: logout())


@presentation.init_for(MainTask, "len(url) >= 3 and url[0] == 'services'")
def init_app__assets(self, url, comp, http_method, request):
    if url[1] in self._services:
        component.Component(self._services[url[1]]).init(url[2:], http_method, request)
    else:
        raise NotFound()
