# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from collections import OrderedDict
import imghdr
import peak.rules

from nagare import ajax
from nagare import presentation, security, editor, component
from nagare.i18n import _, _L

from kansha.authentication.database import validators, forms as registation_forms
from kansha.board import comp as board
from kansha.menu import MenuEntry
from usermanager import UserManager

from .user_cards import UserCards
from kansha import validator

LANGUAGES = {'en': _L('english'),
             'fr': _L('french')}


class UserProfile(object):

    def __init__(self, app_title, app_banner, theme, user, search_engine, services_service):
        """
        In:
         - ``user`` -- user (DataUser instance)
        """
        self.app_title = app_title
        self.menu = OrderedDict()
        self.menu['boards'] = MenuEntry(
            _L(u'Boards'),
            'board',
            services_service(
                UserBoards,
                app_title,
                app_banner,
                theme,
                user,
            )
        )
        self.menu['my-cards'] = MenuEntry(
            _L(u'My cards'),
            'profile',
            services_service(UserCards, user, search_engine, theme)
        )
        self.menu['profile'] = MenuEntry(
            _L(u'Profile'),
            'user',
            services_service(
                get_userform(
                    app_title, app_banner, theme, user.source
                ),
                user,
            )
        )

        self.content = component.Component(None)
        self._on_menu_entry(next(iter(self.menu)))

    def _on_menu_entry(self, id_):
        """Select a configuration menu entry

        In:
            - ``id_`` -- the id of the selected menu entry
        """
        self.content.becomes(self.menu[id_].content)
        self.selected = id_


@presentation.render_for(UserProfile, 'edit')
def render_user_profile__edit(self, h, comp, *args):
    h.head << h.head.title(self.app_title)

    with h.div(class_='home'), h.div(class_='grid-2'):
        h << comp.render(h, 'menu')
        with h.div(class_='boards'):
            h << self.content.on_answer(comp.answer).render(h.AsyncRenderer())
    return h.root


@presentation.render_for(UserProfile, 'menu')
def render_user_profile__menu(self, h, comp, *args):
    with h.div(class_='menu'):
        with h.ul:
            for id_, entry in self.menu.iteritems():
                with h.li:
                    with h.a.action(self._on_menu_entry, id_):
                        h << h.i(class_='icon icon-' + entry.icon)
                        h << h.span(entry.label)
                        if self.selected == id_:
                            h << {'class': 'active'}
    return h.root


class BasicUserForm(editor.Editor):

    """ Basic User Form

    View all fields but you can modify language only
    """

    fields = {'username', 'email', 'fullname', 'language', 'picture', 'display_week_numbers'}

    def __init__(self, target, *args):
        """
        In:
         - ``target`` -- DataUser instance
        """
        super(BasicUserForm, self).__init__(target, self.fields)
        self.display_week_numbers.validate(validator.BoolValidator)

    def commit(self):
        super(BasicUserForm, self).commit(self.fields)

    @property
    def target(self):
        if not self._target:
            self._target = self._get_target()
        return self._target

    @target.setter
    def target(self, value):
        self._target = value
        self._get_target = lambda cls = value.__class__, id_ = value._sa_instance_state.key[
            1]: cls.get(id_)

    def __getstate__(self):
        state = self.__dict__
        state['_target'] = None
        return state

    def pre_action(self):
        """Actions done before form submit

         - Reset display_week_numbers to False
        """
        self.display_week_numbers(False)


@presentation.render_for(BasicUserForm)
def render(self, h, comp, *args):
    h << comp.render(h, "edit")
    return h.root


@presentation.render_for(BasicUserForm, model="edit")
def render(self, h, comp, *args):
    with h.div:
        with h.form.pre_action(self.pre_action):
            with h.ul:
                with h.li:
                    h << _('Username')
                    h << h.input(disabled=True, value=self.username())
                with h.li:
                    h << _('Fullname')
                    h << h.input(disabled=True, value=self.fullname())
                with h.li:
                    h << _('Email')
                    h << h.input(disabled=True, value=self.email())
                with h.li:
                    h << _('Language')
                    with h.select().action(self.language).error(self.language.error):
                        for (id, lang) in LANGUAGES.items():
                            if self.language() == id:
                                h << h.option(_(lang), value=id, selected='')
                            else:
                                h << h.option(_(lang), value=id)
                if self.target.picture:
                    with h.li:
                        h << _('Picture')
                        h << h.div(
                            h.img(src=self.target.picture, class_="avatar big"))

                with h.li:
                    h << h.label(_('Display week numbers in calendars'))
                    h << h.input(type='checkbox').selected(self.display_week_numbers.value).action(self.display_week_numbers)

            with h.div:
                h << h.input(value=_("Save"), class_="btn btn-primary",
                             type='submit').action(self.commit)
    return h.root


def get_userform(app_title, app_banner, theme, source):
    """ Default method to get UserForm Class

    In:
     - ``source`` -- source of user (application, google...)
    """
    return BasicUserForm


class UserForm(BasicUserForm):

    def __init__(self, app_title, app_banner, theme, target, assets_manager_service, mail_sender_service):
        """
        In:
         - ``target`` -- DataUser instance
         - ``mail_sender_service`` -- MailSender service
        """
        super(UserForm, self).__init__(target, self.fields)

        self.app_title = app_title
        self.app_banner = app_banner
        self.theme = theme
        self.mail_sender = mail_sender_service
        self.assets_manager = assets_manager_service
        self.username.validate(self.validate_username)
        self.fullname.validate(validators.validate_non_empty_string)

        # Add other properties (email to confirm, passwords...)
        self.email_to_confirm = editor.Property(
            target.email).validate(validators.validate_email)
        self.old_password = editor.Property(
            '').validate(self.validate_old_password)
        self.password = editor.Property('').validate(self.validate_password)
        self.password_repeat = editor.Property(
            '').validate(self.validate_passwords_match)
        self.user_manager = UserManager()

    def validate_username(self, value):
        """Check username

        In:
         - ``value`` -- username (must be unique)
        Return:
         - username value if username is unique (else raise an exception)
        """
        value = validators.validate_identifier(value)
        # check that this user name does not exist
        user = self.user_manager.get_by_username(value)
        if user:
            raise ValueError(_("Username %s is not available. Please choose another one.")
                             % value)
        return value

    def validate_password(self, value):
        """Check new password

        In:
         - ``value`` -- new password (must be greater than 6 chars)
        Return:
         - password value if password is ok (else raise an exception)
        """
        # check password complexity
        min_len = 6

        if len(value) < min_len and len(value) > 0:
            raise ValueError(_("Password too short: should have at least %d characters")
                             % min_len)
        return value

    def validate_old_password(self, value):
        """Check old password

        In:
         - ``value`` -- old password
        Return:
         - password value if value is the old password
        """
        if len(value) == 0 or security.get_user().data.check_password(value):
            return self.validate_password(value)
        raise ValueError(_("This password doesn't match the old one."))

    def validate_passwords_match(self, value):
        """Check if confirmation password and password are equals

        In:
         - ``value`` -- confirmation password
        Return:
         - password value if confirmation password and password are equals
        """
        if self.password.value == value:
            return value
        else:
            raise ValueError(_("The two passwords don't match"))

    def _create_email_confirmation(self, application_url):
        """Create email confirmation"""
        confirmation_url = '/'.join(
            (application_url, 'new_mail', self.username()))
        return registation_forms.EmailConfirmation(self.app_title, self.app_banner, self.theme, lambda: security.get_user().data, confirmation_url)

    def commit(self, application_url):
        """ Commit method

        If email changes, send confirmation mail to user
        If password changes, check passwords rules
        """
        if not self.is_validated(self.fields):
            return
        # Test if email_to_confirm has changed
        if (self.target.email_to_confirm != self.email_to_confirm() and
                self.target.email != self.email_to_confirm()):
            # Change target email_to_confirm (need it to send mail)
            self.target.email_to_confirm = self.email_to_confirm()
            confirmation = self._create_email_confirmation(application_url)
            confirmation.send_email(self.mail_sender)
            self.email_to_confirm.info = _(
                "A confirmation email has been sent.")
        # Test if password has changed
        if (len(self.password()) > 0 and
                not(self.old_password.error) and
                not(self.password_repeat.error)):
            user = security.get_user()
            user.data.change_password(self.password())
            user.update_password(self.password())
            self.password_repeat.info = _("The password has been changed")
        super(BasicUserForm, self).commit(self.fields)

    def set_picture(self, new_file):
        uid = self.target.username
        self.picture.error = None
        error = None

        # No value, exit
        if new_file == '':
            return None

        try:
            validators.validate_file(
                new_file, self.assets_manager.max_size, _(u'File must be less than %d KB'))
        except ValueError, e:
            error = e.message
        if imghdr.what(new_file.file) is None:
            error = _(u'Invalid image file')

        if error:
            self.picture.error = error
            return None

        # Remove old value
        if self.target.picture:
            self.assets_manager.delete(uid)

        # Save new value
        self.assets_manager.save(new_file.file.read(), file_id=uid, metadata={
            'filename': new_file.filename, 'content-type': new_file.type}, thumb_size=(100, 100))
        self.picture(self.assets_manager.get_image_url(uid, size='thumb'))


@presentation.render_for(UserForm, "edit")
def render(self, h, comp, *args):
    h.head.css_url('css/themes/home.css')
    h.head.css_url('css/themes/%s/home.css' % self.theme)

    with h.div(class_='row'):
        with h.form.pre_action(self.pre_action):
            with h.ul:
                with h.li:
                    h << (_('Username'), ' ',
                          h.input(type='text', readonly=True, value=self.username()))
                with h.li:
                    h << (_('Fullname'), ' ',
                          h.input(type='text', value=self.fullname()).action(self.fullname))
                with h.li:
                    h << (_('Email'), ' ',
                          h.input(type='text', value=self.email_to_confirm()).action(self.email_to_confirm).error(self.email_to_confirm.error))
                    if hasattr(self.email_to_confirm, 'info'):
                        h << h.span(
                            self.email_to_confirm.info, class_="info-message")
                with h.li(_('Language')):
                    with h.select().action(self.language).error(self.language.error):
                        for (id, lang) in LANGUAGES.items():
                            if self.language() == id:
                                h << h.option(lang, value=id, selected='')
                            else:
                                h << h.option(lang, value=id)

                with h.li:
                    h << _('Picture')
                    picture = self.target.get_picture()
                    if picture:
                        with h.label(for_='picture'):
                            h << h.img(
                                src=self.target.get_picture(), class_="avatar big")
                    h << h.input(type='file', id='picture').action(self.set_picture)\
                        .error(self.picture.error)

                with h.li:
                    h << (_('Old Password'), ' ',
                          # FF hack, don't save my password please
                          h.input(type='password', style="display:none"),
                          h.input(type='password').action(self.old_password)
                          .error(self.old_password.error))
                    if hasattr(self.password_repeat, 'info'):
                        h << h.span(
                            self.password_repeat.info, class_="info-message")
                with h.li:
                    h << (_('New password'), ' ',
                          h.input(type='password').action(self.password).error(self.password.error))
                with h.li:
                    h << (_('Repeat new password'), ' ',
                          h.input(type='password').action(self.password_repeat)
                          .error(self.password_repeat.error))

                with h.li:
                    week_numbers_id = h.generate_id('week_numbers_')
                    h << h.label(_('Display week numbers in calendars'), for_=week_numbers_id)
                    h << h.input(type='checkbox', id=week_numbers_id).selected(self.display_week_numbers.value).action(self.display_week_numbers)

            with h.div(class_=''):
                h << h.input(_("Save"),
                             class_="btn btn-primary",
                             type='submit').action(self.commit, h.request.application_url)
    return h.root


@peak.rules.when(get_userform, """source == 'application'""")
def get_userform(app_title, app_banner, theme, source):
    """ User form for application user
    """
    def factory_compatible_with_services(target, services_service):
        return services_service(UserForm, app_title, app_banner, theme, target)

    return factory_compatible_with_services

class ExternalUserForm(BasicUserForm):
    pass


@peak.rules.when(get_userform, """source != 'application'""")
def get_userform(app_title, app_banner, theme, source):
    """ User form for application user
    """
    return ExternalUserForm


class UserBoards(object):

    def __init__(self, app_title, app_banner, theme, user, mail_sender_service, assets_manager_service, services_service):
        """ UserBoards

        List of user's boards, and form to add new one board

        In:
         - ``app_title`` -- Application title
         - ``app_banner`` -- Application banner
         - ``theme`` -- Custom theme name
         - ``user`` -- User whose boards will be listed
         - ``mail_sender`` -- Mail sender
         - ``assets_manager`` -- Assets manager service
        """
        self.app_title = app_title

        self.app_title = app_title
        self.app_banner = app_banner
        self.theme = theme
        self.mail_sender = mail_sender_service
        self.assets_manager = assets_manager_service
        self.user_id = user.username
        self.user_source = user.source
        self._services = services_service
        self.reload_boards()

    def _get_board(self, b, model=0):
        b = self._services(board.Board, b.id, self.app_title, self.app_banner, self.theme,
                           None,
                           on_board_delete=self.reload_boards,
                           on_board_archive=self.reload_boards,
                           on_board_restore=self.reload_boards,
                           on_board_leave=self.reload_boards,
                           on_update_members=self.reload_boards,
                           load_data=False)
        return component.Component(b, model)

    def reload_boards(self):
        self.last_modified_boards = OrderedDict((b.id, self._get_board(b))
                                                for b in board.Board.get_last_modified_boards_for(self.user_id, self.user_source))
        self.my_boards = OrderedDict((b.id, self._get_board(b))
                                     for b in board.Board.get_user_boards_for(self.user_id, self.user_source))
        self.guest_boards = OrderedDict((b.id, self._get_board(b))
                                        for b in board.Board.get_guest_boards_for(self.user_id, self.user_source))
        self.archived_boards = OrderedDict((b.id, self._get_board(b, 'archived_item'))
                                           for b in board.Board.get_archived_boards_for(self.user_id, self.user_source))

    def purge_archived_boards(self):
        for board in self.archived_boards.itervalues():
            board().on_board_delete = None  # don't call self.delete_board!
            board().delete()
        self.archived_boards = OrderedDict()


@presentation.render_for(UserBoards)
def render_userboards(self, h, comp, *args):
    h.head << h.head.title(self.app_title)

    h.head.css_url('css/themes/home.css')
    h.head.css_url('css/themes/%s/home.css' % self.theme)

    if self.last_modified_boards:
        h << h.h1(_(u'Last modified boards'))
        with h.ul(class_="board-labels"):
            h << [b.on_answer(comp.answer).render(h, "item") for b in self.last_modified_boards.itervalues()]

    h << h.h1(_(u'My boards'))
    with h.ul(class_="board-labels"):
        h << [b.on_answer(comp.answer).render(h, "item") for b in self.my_boards.itervalues()]

    if self.guest_boards:
        h << h.h1(_(u'Guest boards'))
        with h.ul(class_="board-labels"):
            h << [b.on_answer(comp.answer).render(h, "item") for b in self.guest_boards.itervalues()]

    with h.div:
        pass # TODO add board templates

    if len(self.archived_boards):
        h << h.h1(_('Archived boards'))

        with h.ul(class_="board-labels"):
            h << [b.render(h, "archived_item")
                  for b in self.archived_boards.itervalues()]

        h << h.button(
            _("Delete"),
            class_="delete",
            onclick='return confirm(%s)' % ajax.py2js(
                _("These boards will be destroyed. Are you sure?")
            ).decode('UTF-8'),
            type='submit'
        ).action(self.purge_archived_boards)

    h << h.script('YAHOO.kansha.app.hideOverlay();'
                  'function reload_boards() { %s; }' % h.AsyncRenderer().a.action(ajax.Update(action=self.reload_boards, render=0)).get('onclick'))

    return h.root
