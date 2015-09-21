# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import hashlib
import textwrap
import time
import webob
from datetime import datetime, timedelta

from nagare import (presentation, editor, component, security, log, database)
from nagare.i18n import _

from . import validators, captcha
from kansha.user import usermanager
from kansha.models import DataToken

UserConfirmationTimeout = timedelta(hours=12)


class Header(object):

    def __init__(self, app_title, app_banner, custom_css):
        self.app_title = app_title
        self.app_banner = app_banner
        self.custom_css = custom_css


@presentation.render_for(Header)
def render_Header(self, h, comp, *args):
    """Head renderer"""

    h.head << h.head.title(self.app_title)
    h.head << h.head.meta(
        name='viewport', content='width=device-width, initial-scale=1.0')

    h.head.css_url('css/knacss.css')
    h.head.css_url('css/login.css')
    if self.custom_css:
        h.head.css_url(self.custom_css)

    with h.div(class_='header'):
        with h.a(href=h.request.application_url):
            h << h.div(class_='logo')
        h << h.h1(self.app_banner)
    return h.root


@presentation.render_for(Header, 'hide')
def render_Header_hide(self, h, comp, *args):
    h.head.css('hide_logins', u'''.body-login .oauthLogin, .body-login .LDAPLogin,  .body-login .databaseLogin {display:none;}''')
    return h.root


def redirect_to(url):
    raise webob.exc.HTTPSeeOther(location=url)


class Login(object):

    def __init__(self, app_title, app_banner, custom_css, mail_sender, config):
        self._error_message = ''
        self.registration_task = RegistrationTask(app_title, app_banner, custom_css, mail_sender, config['moderator'])
        self.default_username = config['default_username']
        self.default_password = config['default_password']
        self.pwd_reset = PasswordResetTask(app_title, app_banner, custom_css, mail_sender)
        self.content = component.Component()

    @property
    def alt_title(self):
        'Return a unicode to overwrite default login page title, or None.'
        return None or getattr(self.content(), 'alt_title', None)

    @property
    def error_message(self):
        return self._error_message or getattr(self.content(), 'error_message', u'')

    @error_message.setter
    def error_message(self, value):
        self._error_message = value
        if self.content():
            setattr(self.content(), 'error_message', u'')

    def log_in(self, comp):
        u = security.get_user()
        # If user is not local user remove user from security
        if u and not u.is_local:
            security.set_user(None)
            u = None
        if u is not None:
            database.session.flush()
            comp.answer(u)
        else:
            self._error_message = _('Login failed')


@presentation.render_for(Login)
def render_Login(self, h, comp, *args):
    if self.content() is not None:
        return self.content
    else:
        return comp.render(h, 'form')


@presentation.render_for(Login, 'form')
def render_Login_form(self, h, comp, *args):
    with h.div(class_='databaseLogin'):
        with h.form:
            # if self.error_message:
            #     h << h.br << h.div(self.error_message, class_="error")
            h << h.input(type='text', name='__ac_name', id="username",
                         value=self.default_username, placeholder=_("Enter username"))
            h << h.input(type='password', name='__ac_password', id="password",
                         value=self.default_password, placeholder=_("Enter password"))
            h << h.a(_('Forgot password?')).action(self.content.call, self.pwd_reset)
            with h.div(class_='actions'):
                h << h.input(type='submit', value=_(u'Sign in'), class_="btn btn-primary btn-small").action(self.log_in, comp)
                with h.div:
                    h << _('No account yet? ')
                    h << h.a(_('Sign up')).action(self.content.call, self.registration_task)
    return h.root


class RegistrationForm(editor.Editor):

    """Registration form for creating a new (unconfirmed) user"""

    def __init__(self, app_title, app_banner, custom_css):
        self.username = editor.Property('').validate(self.validate_username)
        self.email = editor.Property('').validate(validators.validate_email)
        self.fullname = editor.Property('').validate(validators.validate_non_empty_string)
        self.password = editor.Property('').validate(validators.validate_password)
        self.password_repeat = editor.Property('').validate(validators.validate_password)
        self.init_captcha_image()
        self.captcha_text = editor.Property('').validate(self.validate_captcha)
        self.header = component.Component(Header(app_title, app_banner, custom_css))
        self.user_manager = usermanager.UserManager()
        self.error_message = u''
        self.alt_title = _(u'Sign up')

    def init_captcha_image(self):
        self.captcha_image = component.Component(captcha.Captcha())
        self.captcha_date = datetime.now()

    def validate_username(self, value):
        value = validators.validate_identifier(value)
        # check that this user name does not exist
        u = usermanager.UserManager.get_by_username(value)
        if u:
            raise ValueError(_("Username %s is not available. Please choose another one.")
                             % value)
        return value

    def validate_captcha(self, value):
        # validate the text
        if not value or (value.lower() != self.captcha_image().text.lower()):
            self.init_captcha_image()
            raise ValueError(_("Invalid captcha"))

        # check the expiration date
        captcha_expiration = timedelta(minutes=10)
        if (datetime.now() - self.captcha_date) > captcha_expiration:
            self.init_captcha_image()
            raise ValueError(_("Entered too late"))
        return value

    def validate_passwords_match(self):
        if self.password.value != self.password_repeat.value:
            self.password_repeat.error = _("The two passwords don't match")

    def commit(self):

        properties = ('username', 'fullname', 'email', 'password',
                      'password_repeat', 'captcha_text')
        if not self.is_validated(properties):
            self.captcha_image.becomes(captcha.Captcha())
            self.error_message = _(u'Unable to process. Check your input below.')
            return None

        # register the user in the database
        u = self.user_manager.create_user(username=self.username.value,
                                          password=self.password.value,
                                          fullname=self.fullname.value,
                                          email=self.email.value)
        return u

    def on_ok(self, comp):
        u = self.commit()
        if u:
            comp.answer(u.username)


@presentation.render_for(RegistrationForm)
def render_RegistrationForm(self, h, comp, *args):
    h << self.header.render(h, 'hide')
    with h.div(class_='regForm'):
        # autocomplete="off": do not store the password
        with h.form(autocomplete="off").post_action(self.validate_passwords_match):
            with h.div(class_='fields'):
                fields = (
                    (_('Username'), 'username', 'text', self.username),
                    (_('Email address'), 'email', 'text', self.email),
                    (_('Fullname'), 'fullname', 'text', self.fullname),
                    (_('Password'),
                        'password', 'password', self.password),
                    (_('Password (repeat)'), 'password-repeat',
                        'password', self.password_repeat)
                )
                for label, css_class, input_type, property in fields:
                    with h.div(class_='%s-field field' % css_class):
                        id_ = h.generate_id("field")
                        with h.label(for_=id_):
                            h << label
                        h << h.input(id=id_,
                                     type=input_type,
                                     value=property()).action(property).error(property.error)

                with h.div(class_='captcha-field field'):
                    id_ = h.generate_id("field")
                    with h.label(for_=id_):
                        h << _("Enter the captcha text")
                    h << h.input(id=id_,
                                 type='text').action(self.captcha_text).error(self.captcha_text.error)
                h << comp.render(h.AsyncRenderer(), 'captcha')
            with h.div(class_='actions'):
                h << h.input(type='submit',
                             value=_("Create new account"),
                             class_="btn btn-primary btn-small").action(self.on_ok, comp)

            h << _("Already have an account? ") << h.a(
                _("Log in")).action(comp.answer)

    return h.root


@presentation.render_for(RegistrationForm, 'captcha')
def render_RegistrationForm_captcha(self, h, comp, *args):
    with h.div(id='captchaImage'):
        h << self.captcha_image
        h << h.a(id="captchaRefresh", title=_("refresh captcha")).action(self.init_captcha_image)
    return h.root
# ----------------------------------------------------------


class EmailRegistrationForm(editor.Editor):

    """Registration form for creating a new (unconfirmed) user"""

    def __init__(self, app_title, app_banner, custom_css, username):
        self.email = editor.Property('').validate(validators.validate_email)
        self.email_repeat = editor.Property('').validate(validators.validate_email)
        self.header = component.Component(Header(app_title, app_banner, custom_css))
        self.error_message = u''
        self.username = username
        self.app_title = app_title

    def validate_emails_match(self):
        if self.email.value != self.email_repeat.value:
            self.email_repeat.error = _("The two emails don't match")

    def commit(self):

        properties = ('email', 'email_repeat')
        if not self.is_validated(properties):
            self.error_message = _(u'Unable to process. Check your input below.')
            return None

        u = usermanager.UserManager.get_by_username(self.username)
        if u:
            u.set_email_to_confirm(self.email.value)
            return self.username

        self.error_message = _(u'Something went wrong: user does not exist! Please contact the administrator of this site.')
        return None

    def on_ok(self, comp):
        email = self.commit()
        if email:
            comp.answer(email)


@presentation.render_for(EmailRegistrationForm)
def render_RegistrationForm(self, h, comp, *args):
    h << self.header.render(h, 'hide')
    with h.div(class_='regForm'):
        # autocomplete="off": do not store the password
        with h.form(autocomplete="off").post_action(self.validate_emails_match):
            h << h.p(_(u'Your profile is missing an email address. You have to enter a valid email address to open an account on %s') % self.app_title)
            with h.div(class_='fields'):
                fields = (
                    (_('Email address'), 'email', 'text', self.email),
                    (_('Email address (repeat)'), 'email', 'text', self.email_repeat),
                )
                for label, css_class, input_type, property in fields:
                    with h.div(class_='%s-field field' % css_class):
                        id_ = h.generate_id("field")
                        with h.label(for_=id_):
                            h << label
                        h << h.input(id=id_,
                                     type=input_type,
                                     value=property()).action(property).error(property.error)

            with h.div(class_='actions'):
                h << h.input(type='submit',
                             value=_("Create new account"),
                             class_="btn btn-primary btn-small").action(self.on_ok, comp)

            h << _("Already have an account? ") << h.a(
                _("Log in")).action(comp.answer)

    return h.root

# -----------------------------------------------------------------------


class RegistrationConfirmation(object):

    """Confirm a registration by sending a confirmation email, then acknowledge the success/failure
    of the operation"""

    def __init__(self, app_title, app_banner, custom_css):
        self.app_title = app_title
        self.header = component.Component(Header(app_title, app_banner, custom_css))


@presentation.render_for(RegistrationConfirmation, model='success')
def render_registration_confirmation_success(self, h, comp, *args):
    """Renders an registration acknowledgment message"""
    with h.body(class_='body-login'):
        h << self.header
        with h.div(class_='title'):
            h << h.h2(_(u'Sign up'))

        with h.div(class_='container'):
            with h.h3:
                h << _("Registration successful!")

            with h.p:
                h << _("""You are now a registered user of %s. You can login
                on the home page of the application.""") % self.app_title

            with h.form:
                with h.div(class_='actions'):
                    h << h.input(type='submit',
                                 class_="btn btn-primary btn-small",
                                 value=_("Ok")).action(comp.answer)

    return h.root


@presentation.render_for(RegistrationConfirmation, model='failure')
def render_registration_confirmation_failure(self, h, comp, *args):
    with h.body(class_='body-login'):
        h << self.header
        with h.div(class_='title'):
            h << h.h2(_(u'Sign up'))
            h << h.small(_("Registration failure!"), class_='error')
        with h.div(class_='container'):
            with h.p:
                h << _("""Registration failure! The token received is either expired or invalid. Please register again.""")

            with h.form:
                with h.div(class_='actions'):
                    h << h.input(type='submit', class_="btn btn-primary btn-small",
                                 value=_("Ok")).action(comp.answer)

    return h.root


# ----------------------------------------------------------

class PasswordEditor(editor.Editor):

    """Password editor, so that users can edit their password"""

    def __init__(self, app_title, app_banner, custom_css, get_user, check_old_password=True):
        self._get_user = get_user
        self.check_old_password = check_old_password
        self.old_password = editor.Property(
            '').validate(self.validate_old_password)
        self.password = editor.Property(
            '').validate(validators.validate_password)
        self.password_repeat = editor.Property(
            '').validate(validators.validate_password)
        self.header = component.Component(Header(app_title, app_banner, custom_css))
        self.error_message = u''

    def validate_old_password(self, value):
        validators.validate_non_empty_string(value)
        if not self.user.check_password(value):
            raise ValueError(_("Invalid password"))
        return value

    def validate_passwords_match(self):
        if self.password.value != self.password_repeat.value:
            self.password_repeat.error = _("The two passwords don't match")

    @property
    def user(self):
        return self._get_user()

    def commit(self):
        properties = ['password', 'password_repeat']
        if self.check_old_password:
            properties.insert(0, 'old_password')

        if not self.is_validated(properties):
            self.error_message = _(u'Invalid input!')
            return False

        # change the user's password in the database
        self.user.change_password(self.password.value)

        # change the current user credentials if applicable
        current_user = security.get_user()
        if current_user and (current_user.entity is self.user):
            current_user.update_password(self.password.value)

        return True


@presentation.render_for(PasswordEditor)
def render_password_editor(self, h, comp, *args):
    def commit():
        if self.commit():
            comp.answer(True)

    with h.body(class_='body-login'):
        h << self.header
        with h.div(class_='title'):
            h << h.h2(_(u'Change password'))
            if self.error_message:
                h << h.small(self.error_message, class_='error')
                self.error_message = u''
        with h.div(class_='container'):

            # autocomplete="off" prevent IE & Firefox from remembering the
            # passwords
            with h.form(autocomplete="off").post_action(self.validate_passwords_match):
                with h.div(class_='fields'):
                    fields = [
                        (_('Password'),
                            'password', 'password', self.password),
                        (_('Password (repeat)'), 'password-repeat',
                            'password', self.password_repeat)
                    ]
                    old_password_field = (_('Old Password'),
                                          'old-password', 'password', self.old_password)
                    if self.check_old_password:
                        fields.insert(0, old_password_field)

                    for label, css_class, input_type, property in fields:
                        with h.div(class_='%s-field field' % css_class):
                            id = h.generate_id("field")
                            with h.label(for_=id):
                                h << label
                            h << h.input(id=id,
                                         type=input_type,
                                         value=property()).action(property).error(property.error)

                with h.div(class_='actions'):
                    h << h.input(type='submit',
                                 value=_("Change password"),
                                 class_='btn btn-primary btn-small').action(commit)
                    h << u' '
                    h << h.input(type='submit',
                                 value=_("Cancel"),
                                 class_='btn btn-small').action(comp.answer)

        return h.root


# ----------------------------------------------------------

class PasswordResetForm(editor.Editor):

    """Password reset form, ask the user email"""

    def __init__(self, app_title, app_banner, custom_css, get_user_by_username):
        self._get_user_by_username = get_user_by_username
        self.username = editor.Property('').validate(self.validate_username)
        self.email = editor.Property('').validate(validators.validate_email)
        self.header = component.Component(Header(app_title, app_banner, custom_css))
        self.error_message = u''

    def validate_username(self, value):
        value = validators.validate_identifier(value)

        user = self._get_user_by_username(value)
        if not user:
            raise ValueError(
                _("This username is not registered on our database"))
        if user.source != 'application':
            raise ValueError(
                _("You can not change your password since you log in by an external service."))
        return value

    def validate_email_match_user_email(self):
        if self.username.error or self.email.error:  # there are errors already
            return

        user = self._get_user_by_username(self.username.value)
        if self.email() != user.email:
            self.email.error = _(
                "This email address does not match the user's email address")

    def commit(self):
        properties = ('username', 'email')
        if not self.is_validated(properties):
            self.error_message = _(u'Invalid input!')
            return None

        return self._get_user_by_username(self.username.value)


@presentation.render_for(PasswordResetForm)
def render_password_reset_form(self, h, comp, *args):
    def commit():
        user = self.commit()
        if user:
            comp.answer(user.username)
    h << self.header.render(h, 'hide')
    with h.div(class_='regForm'):

        with h.p:
            h << _("""Please enter your username and your email address and you'll receive an email that contains a link to reset your password.""")

        with h.form.post_action(self.validate_email_match_user_email):
            with h.div(class_='fields'):
                fields = (
                    (_('Username'), 'username', 'text', self.username),
                    (_('Email address'), 'email', 'text', self.email),
                )
                for label, css_class, input_type, property in fields:
                    with h.div(class_='%s-field field' % css_class):
                        id = h.generate_id("field")
                        with h.label(for_=id):
                            h << label
                        h << h.input(id=id,
                                     type=input_type,
                                     value=property()).action(property).error(property.error)

            with h.div(class_='actions'):
                h << h.input(type='submit',
                             value=_("Reset password"),
                             class_='btn btn-primary btn-small').action(commit)

            h << (_("Remember your password?"), u' ', h.a(_("Log in")).action(comp.answer))

    return h.root


# ----------------------------------------------------------

class PasswordResetConfirmation(object):

    """Confirm a password reset by sending a confirmation email, then acknowledge the
    success/failure of the operation"""

    def __init__(self, app_title, app_banner, custom_css, get_user, confirmation_base_url):
        self.app_title = app_title
        self._get_user = get_user
        self.confirmation_base_url = confirmation_base_url
        self.token_generator = TokenGenerator(self._get_user().username, u'reset_password')
        self.header = component.Component(Header(self.app_title, app_banner, custom_css))
        self.alt_title = _(u'Reset password')

    @property
    def user(self):
        return self._get_user()

    @property
    def confirmation_url(self):
        token = self.token_generator.create_token().token
        return '/'.join((self.confirmation_base_url, 'reset', self._get_user().username, token))

    def confirm_password_reset(self, token):
        return self.token_generator.check_token(token)

    def reset_token(self, token):
        return self.token_generator.reset_token(token)

    def send_email(self, mail_sender):
        subst = dict(fullname=self.user.fullname,
                     app_title=self.app_title,
                     confirmation_url=self.confirmation_url)

        message = _("""
        Hello %(fullname)s,

        We received a request to reset your password. If you are at the origin of this
        request, please click on this confirmation link: %(confirmation_url)s. Otherwise,
        feel free to ignore this email.

        See you soon on %(app_title)s.
        """) % subst

        mail_sender.send(_("%(app_title)s: Password Reset") % subst,
                         [self.user.email],
                         textwrap.dedent(message).strip())


@presentation.render_for(PasswordResetConfirmation, model='success')
def render_password_reset_confirmation_failure(self, h, comp, *args):
    """Renders a password change acknowledgment message"""
    with h.body(class_='body-login'):
        h << self.header
        with h.div(class_='title'):
            h << h.h2(_(u'Change password'))

        with h.div(class_='container'):
            with h.h3:
                h << _("Password change successful!")

            with h.p:
                h << _("""Your password have been changed successfully.""")

            with h.form:
                with h.div(class_='actions'):
                    h << h.input(type='submit',
                                 class_='btn btn-primary btn-small',
                                 value=_("Ok")).action(comp.answer)
    return h.root


@presentation.render_for(PasswordResetConfirmation, model='email')
def render_password_reset_confirmation_failure(self, h, comp, *args):
    """Renders a password change acknowledgment message"""
    h << self.header.render(h, 'hide')
    with h.div(class_='regForm'):
        with h.h3:
            h << _("Email sent!")

        with h.p:
            h << _("""An email has been sent!""")

        with h.form:
            with h.div(class_='actions'):
                h << h.input(type='submit',
                             class_='btn btn-primary btn-small',
                             value=_("Ok")).action(comp.answer)
    return h.root


@presentation.render_for(PasswordResetConfirmation, model='failure')
def render_password_reset_confirmation_failure(self, h, comp, *args):
    with h.body(class_='body-login'):
        h << self.header
        with h.div(class_='title'):
            h << h.h2(_(u'Change password'))
            h << h.small(_("Password reset failure!"), class_='error')
        with h.div(class_='container'):
            with h.p:
                h << _("""Password reset failure! Please try again.""")

            with h.form:
                with h.div(class_='actions'):
                    h << h.input(type='submit',
                                 class_='btn btn-primary btn-small',
                                 value=_("Ok")).action(comp.answer)

    return h.root


# ----------------------------------------------------------

class EmailConfirmation(object):

    """Confirm a user email address by sending an email to the user with a confirmation link."""

    def __init__(self, app_title, app_banner, custom_css, get_user, confirmation_base_url='', moderator=''):
        self.app_title = app_title
        self._get_user = get_user
        self.moderator = moderator
        self.confirmation_base_url = confirmation_base_url
        self.token_generator = TokenGenerator(self._get_user().username, 'email_confirmation')
        self.header = component.Component(Header(app_title, app_banner, custom_css))
        self.alt_title = _('Sign up')

    @property
    def user(self):
        return self._get_user()

    def confirm_email_address(self, token):
        # too late, the user has been removed from the database
        if not self.user:
            return False

        # valid token?
        if not self.token_generator.check_token(token):
            return False

        self.user.confirm_email()

        return True

    def reset_token(self, token):
        return self.token_generator.reset_token(token)

    @property
    def confirmation_url(self):
        token = self.token_generator.create_token().token
        return '/'.join((self.confirmation_base_url, token))

    def send_email(self, mail_sender):
        '''
        If the email address ``true_dest`` is given, send the mail to
        that person instead of self.user.
        '''

        subst = dict(fullname=self.user.fullname,
                     login=self.user.username,
                     email=self.user.email_to_confirm,
                     app_title=self.app_title,
                     confirmation_url=self.confirmation_url)

        if self.moderator:
            message = _("""
            Hello moderator,

            %(fullname)s is willing to register an account (%(login)s) on the %(app_title)s application.

            Her (his) email address is %(email)s. Please verify it before accepting this account creation.

            In order to confirm that email address and accept the user's registration,
            please click on this confirmation link: %(confirmation_url)s.

            If you don't accept this request, feel free to ignore this email.
            Nothing will change into the user's pending account until your click
            on the confirmation link.

            Once confirmed, the user can login with her (his) login "%(login)s" and
            the password she (he) provided.
            """) % subst
            subject = _("%(app_title)s: Confirm user registration") % subst
        else:
            message = _("""
            Hello %(fullname)s,

            In order to confirm your email address in the %(app_title)s application,
            please click on this confirmation link: %(confirmation_url)s.

            If you are not at the origin of this request, feel free to ignore this
            email. Nothing will change into your account until your click on the
            confirmation link.

            Once confirmed, you can login with your login "%(login)s" and the password you just provided.

            See you soon on %(app_title)s.
            """) % subst
            subject = _("%(app_title)s: Confirm your email address") % subst

        mail_sender.send(subject,
                         [self.moderator if self.moderator else self.user.email_to_confirm],
                         textwrap.dedent(message).strip())


@presentation.render_for(EmailConfirmation)
def render_registration_confirmation(self, h, comp, *args):
    h << self.header.render(h, 'hide')
    with h.div(class_='regForm'):
        with h.h3:
            h << _("Registration request sent") if self.moderator else _("Confirm your email address!")

        with h.p:
            if self.moderator:
                h << _("""An email has been sent to the moderator. You will be contacted when
                your account is activated.""")
            else:
                h << _("""An email has been sent to your email address. You have to click on the
                confirmation link in this email in order to confirm your email address in the
                application.""")

        with h.form:
            with h.div(class_='actions'):
                h << h.input(type='submit',
                             class_='btn btn-primary btn-small',
                             value=_("Ok")).action(comp.answer)

    return h.root


# ----------------------------------------------------------

class EmailInvitation(object):

    """Send invitation email to the user with a confirmation link."""

    def __init__(self, app_title, app_banner, custom_css, email, host, board, confirmation_base_url):
        """ Initialization method

        In:
         - ``email`` -- email of the guest
         - ``home`` -- host (DataUser instance)
         - ``board`` -- target of invitation (DataBoard instance)
         - ``confirmation_base_url`` -- base url for confirmation link
        """
        self.app_title = app_title
        self.email = email
        self.confirmation_base_url = confirmation_base_url
        self.host = host
        self.board = board
        self.header = component.Component(Header(app_title, app_banner, custom_css))
        self.token_generator = TokenGenerator(email,
                                              u'invite board %s' % board.id, expiration_delay=timedelta(days=2))

    @property
    def confirmation_url(self):
        who = usermanager.UserManager.get_by_email(self.email)
        if who is None:
            token = self.token_generator.create_token()
            self.board.pending.append(token)
        else:
            who.add_board(self.board)
        return u'/'.join((self.confirmation_base_url, self.board.url))

    def send_email(self, mail_sender):
        subst = dict(app_title=self.app_title,
                     board_title=self.board.title,
                     email=self.email,
                     host_name=self.host.fullname,
                     host_email=self.host.email,
                     confirmation_url=self.confirmation_url)

        message = _("""
        Hello,

        You were invited by %(host_name)s (%(host_email)s) to the board "%(board_title)s".

        To view the board, click on this link : %(confirmation_url)s.

        If you don't already have an account, register with email %(email)s and you will automatically join the board.

        See you soon on %(app_title)s.
        """) % subst

        mail_sender.send(_('%(app_title)s: Invitation to the board "%(board_title)s"') % subst,
                         [self.email],
                         textwrap.dedent(message).strip())

# ----------------------------------------------------------


class RegistrationTask(component.Task):

    """A task that handles the user registration process"""

    def __init__(self, app_title, app_banner, custom_css, mail_sender, moderator='', username=''):
        '''
        Register a new user (`username` not provided)
        or register email for an existing unconfirmed user (`username` provided).
        If `moderator` is set to an email address, all confirmation requests are sent there instead of user's email.
        '''
        self.app_title = app_title
        self.app_banner = app_banner
        self.custom_css = custom_css
        self.mail_sender = mail_sender
        self.moderator = moderator
        self.confirmation_base_url = mail_sender.application_url
        self.state = None  # task state, initialized by a URL rule
        self.user_manager = usermanager.UserManager()
        self.username = username
        self.alt_title = _(u'Sign up')

    def _create_email_confirmation(self, username):
        confirmation_url = '/'.join((self.confirmation_base_url, 'register', username))
        get_user = lambda: usermanager.UserManager.get_by_username(username)
        return EmailConfirmation(self.app_title, self.app_banner, self.custom_css, get_user, confirmation_url, self.moderator)

    def go(self, comp):
        if not self.state:
            # step 1:
            # - ask the user to fill a registration form
            # - send him a confirmation email
            if self.username:
                username = comp.call(
                    EmailRegistrationForm(
                        self.app_title,
                        self.app_banner,
                        self.custom_css,
                        self.username
                    )
                )
            else:
                username = comp.call(RegistrationForm(self.app_title, self.app_banner, self.custom_css))
            if username:
                confirmation = self._create_email_confirmation(username)
                confirmation.send_email(self.mail_sender)
                comp.call(confirmation)
        else:
            # step 2: the user confirms his email by clicking on the
            # confirmation link
            # - check the token (to avoid cheating)
            # - show a confirmation screen
            username, token = self.state

            confirmation = self._create_email_confirmation(username)
            if confirmation.confirm_email_address(token):
                log.debug(_("Registration successful for user %s") % username)
                comp.call(RegistrationConfirmation(self.app_title, self.app_banner, self.custom_css), model='success')
            else:
                log.debug(_("Registration failure for user %s") % username)
                comp.call(RegistrationConfirmation(self.app_title, self.app_banner, self.custom_css), model='failure')

            redirect_to(self.confirmation_base_url)

# ----------------------------------------------------------


class TokenGenerator(object):

    """Generate or check tokens"""

    def __init__(self, username, action, expiration_delay=UserConfirmationTimeout):
        """Create a token generator"""
        self.action = action
        self.username = username
        self.expiration_delay = expiration_delay

    def create_token(self):
        """Create a time-stamped token"""
        token = unicode(
            hashlib.sha512(str(time.time()) + self.username).hexdigest())

        DataToken.delete_token_by_username(self.username, self.action)
        # create new one
        token_instance = DataToken(token=token,
                                   username=self.username,
                                   action=self.action,
                                   date=datetime.now() + self.expiration_delay)
        return token_instance

    def get_tokens(self):
        query = DataToken.query.filter_by(username=self.username)
        query = query.filter(DataToken.action.like(self.action + '%'))
        return query

    def check_token(self, token):
        """Check that the token is valid"""
        t = DataToken.get(token)
        return t and datetime.now() <= t.date

    def reset_token(self, token):
        DataToken.get(token).delete()

# ----------------------------------------------------------


class PasswordResetTask(component.Task):

    """A task that handles the password reset process"""

    def __init__(self, app_title, app_banner, custom_css, mail_sender):
        """Be careful! The confirmation URL *should* be rooted"""
        self.app_title = app_title
        self.app_banner = app_banner
        self.custom_css = custom_css
        self.mail_sender = mail_sender
        self.confirmation_base_url = mail_sender.application_url
        self.state = None  # task state, initialized by a URL rule
        self.user_manager = usermanager.UserManager()
        self.alt_title = _(u'Reset password')

    def _get_user(self, username):
        return usermanager.UserManager.get_by_username(username)

    def _create_password_reset_confirmation(self, username):
        return PasswordResetConfirmation(self.app_title, self.app_banner, self.custom_css,
                                         lambda: self._get_user(username),
                                         self.confirmation_base_url)

    def go(self, comp):
        if not self.state:
            # step 1:
            # - ask the user email
            # - send him a confirmation email
            username = comp.call(PasswordResetForm(self.app_title,
                                                   self.app_banner,
                                                   self.custom_css,
                                                   self._get_user))
            if username:
                confirmation = self._create_password_reset_confirmation(
                    username)
                confirmation.send_email(self.mail_sender)
                comp.call(confirmation, model='email')
                redirect_to(self.confirmation_base_url)
        else:
            # step 2: the user clicked on the confirmation link on his email
            # - check the token (to avoid cheating)
            # - ask for the new password
            username, token = self.state

            confirmation = self._create_password_reset_confirmation(username)
            if confirmation.confirm_password_reset(token):
                log.debug(_("Resetting the password for user %s") % username)
                ret = comp.call(PasswordEditor(self.app_title, self.app_banner, self.custom_css,
                                         lambda username=username: self._get_user(username),
                                         check_old_password=False))
                if ret:
                    confirmation.reset_token(token)
                    comp.call(confirmation, model='success')

            else:
                log.debug(_("Password reset failure for user %s") % username)
                comp.call(confirmation, model='failure')

            redirect_to(self.confirmation_base_url)


@presentation.init_for(PasswordResetTask, "len(url) == 2")
def init_password_reset_task(self, url, comp, http_method, request):
    self.state = (url[0], url[1])


# ----------------------------------------------------------

class ChangeEmailConfirmation(object):

    def __init__(self, app_title, app_banner, custom_css, redirect_url='/'):
        self.redirect_url = redirect_url
        self.header = component.Component(Header(app_title, app_banner, custom_css))


@presentation.render_for(ChangeEmailConfirmation, 'success')
@presentation.render_for(ChangeEmailConfirmation, 'failure')
def render_change_email_confirmation_success(self, h, comp, model):
    """Renders an email change acknowledgment message"""
    with h.body(class_='body-login'):
        h << self.header
        with h.div(class_='title'):
            h << h.h2(_(u'Change email'))

        with h.div(class_='container'):
            with h.h3:
                if model == 'success':
                    h << _("Email change successful!")
                else:
                    h << _("Email change failure!")

            with h.p:
                if model == 'success':
                    h << _("""Your email have been changed successfully.""")
                else:
                    h << _("""Email change failure! Please retry.""")

            with h.form:
                with h.div(class_='actions'):
                    h << h.input(type='submit',
                                 class_='btn btn-primary btn-small',
                                 value=_("Ok")).action(lambda: redirect_to(self.redirect_url))

    return h.root



