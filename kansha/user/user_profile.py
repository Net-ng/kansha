# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import collections
import functools
import imghdr
import urllib
import peak.rules

from nagare import presentation, security, editor, component, database
from nagare.i18n import _, _L

from kansha.authentication.database import validators, forms as registation_forms
from kansha import models
from kansha.board import comp as board
from usermanager import UserManager
from kansha.user.usermanager import get_app_user

from .user_cards import UserCards
from kansha import validator

LANGUAGES = {'en': _L('english'),
             'fr': _L('french')}


MenuEntry = collections.namedtuple('MenuEntry', 'label content')


class UserProfile(object):

    def __init__(self, app_title, app_banner, custom_css, user, mail_sender, assets_manager, search_engine):
        """
        In:
         - ``user`` -- user (DataUser instance)
         - ``mail_sender`` -- MailSender instance
        """
        self.app_title = app_title
        self.menu = collections.OrderedDict()
        self.menu['boards'] = MenuEntry(
            _L(u'Boards'),
            UserBoards(
                app_title,
                app_banner,
                custom_css,
                [dbm.board for dbm in user.board_members],
                mail_sender,
                assets_manager
            )
        )
        self.menu['my-cards'] = MenuEntry(
            _L(u'My cards'),
            UserCards(user, assets_manager, search_engine)
        )
        self.menu['profile'] = MenuEntry(
            _L(u'Profile'),
            get_userform(
                app_title, app_banner, custom_css, user.source
            )(user, mail_sender, assets_manager)
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

    with h.div(id='home-user'), h.div(class_='row-fluid'):
        with h.div(class_='span4'):
            h << comp.render(h, 'menu')
        with h.div(class_='span8'):
            h << self.content.on_answer(comp.answer)
    return h.root


@presentation.render_for(UserProfile, 'menu')
def render_user_profile__menu(self, h, comp, *args):
    return h.ul(
        h.li(
            h.a(
                entry.label,
                class_=(
                    'active {}'.format(id_)
                    if id_ == self.selected
                    else id_
                )
            ).action(self._on_menu_entry, id_)
        )
        for id_, entry in self.menu.iteritems()
    )


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
    with h.div(class_='row-fluid span8'):
        with h.form.pre_action(self.pre_action):
            with h.ul(class_='unstyled'):
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
                h << h.input(value=_("Save"), class_="btn btn-primary btn-small",
                             type='submit').action(self.commit)
    return h.root


def get_userform(app_title, app_banner, custom_css, source):
    """ Default method to get UserForm Class

    In:
     - ``source`` -- source of user (application, google...)
    """
    return BasicUserForm


class UserForm(BasicUserForm):

    def __init__(self, app_title, app_banner, custom_css, target, mail_sender, assets_manager):
        """
        In:
         - ``target`` -- DataUser instance
         - ``mail_sender`` -- MailSender instance
        """
        super(UserForm, self).__init__(target, self.fields)

        self.app_title = app_title
        self.app_banner = app_banner
        self.custom_css = custom_css
        self.mail_sender = mail_sender
        self.assets_manager = assets_manager
        self.application_url = mail_sender.application_url

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

    def _create_email_confirmation(self):
        """Create email confirmation"""
        confirmation_url = '/'.join(
            (self.application_url, 'new_mail', self.username()))
        return registation_forms.EmailConfirmation(self.app_title, self.app_banner, self.custom_css, lambda: security.get_user().data, confirmation_url)

    def commit(self):
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
            confirmation = self._create_email_confirmation()
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
    with h.div(class_='row-fluid span8'):
        with h.form.pre_action(self.pre_action):
            with h.ul(class_='unstyled'):
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
                             class_="btn btn-primary btn-small",
                             type='submit').action(self.commit)
    return h.root


@peak.rules.when(get_userform, """source == 'application'""")
def get_userform(app_title, app_banner, custom_css, source):
    """ User form for application user
    """
    return functools.partial(UserForm, app_title, app_banner, custom_css)


class UserBoards(object):

    def __init__(self, app_title, app_banner, custom_css, boards, mail_sender, assets_manager):
        """ UserBoards

        List of user's boards, and form to add new one board

        In:
         - ``boards`` -- list of user boards (BoardData instances)
        """
        self.app_title = app_title
        self.boards = []
        self.archived_boards = []

        for b in boards:
            _b = board.Board(b.id, app_title, app_banner, custom_css, mail_sender, assets_manager, None,
                             on_board_delete=lambda id_=b.id: self.delete_board(
                                 id_),
                             on_board_archive=lambda id_=b.id: self.archive_board(
                                 id_),
                             on_board_restore=lambda id_=b.id: self.restore_board(
                                 id_),
                             on_board_leave=lambda id_=b.id: self.leave_board(
                                 id_),
                             load_data=False)
            if not b.archived:
                self.boards.append(component.Component(_b))
            elif b.has_manager(security.get_user()):
                self.archived_boards.append(component.Component(_b))

        self.new_board = component.Component(board.NewBoard())

    def archive_board(self, board_id):
        """ switch board from boards list to archived boards list"""
        board_index = None
        for index, comp in enumerate(self.boards):
            if comp().id == board_id:
                board_index = index
                break
        if board_index is not None:
            board = self.boards.pop(board_index)
            self.archived_boards.append(board)

    def restore_board(self, board_id):
        """ switch board from archived boards list to boards list"""
        archived_board_index = None
        for index, comp in enumerate(self.archived_boards):
            if comp().id == board_id:
                archived_board_index = index
                break

        if archived_board_index is not None:
            archived_board = self.archived_boards.pop(archived_board_index)
            self.boards.append(archived_board)

    def delete_board(self, board_id):
        """ remove board from archived boards list"""
        archived_board_index = None
        for index, comp in enumerate(self.archived_boards):
            if comp().id == board_id:
                archived_board_index = index
                break
        if archived_board_index is not None:
            self.archived_boards.pop(archived_board_index)

    def leave_board(self, board_id):
        """ remove board from list """
        board_index = None
        for index, comp in enumerate(self.boards):
            if comp().id == board_id:
                board_index = index
                break
        if board_index is not None:
            self.boards.pop(board_index)

    def purge_archived_boards(self):
        for board in self.archived_boards:
            board().on_board_delete = None  # don't call self.delete_board!
            board().delete()
        self.archived_boards = []


@presentation.render_for(UserBoards)
def render_userboards(self, h, comp, *args):
    h.head << h.head.title(self.app_title)

    with h.ul(class_="unstyled board-labels"):
        h << [b.on_answer(comp.answer).render(h, "item") for b in self.boards]

    with h.div:
        h << self.new_board.on_answer(comp.answer)

    if len(self.archived_boards):
        with h.div:
            h << h.h2(_('Archived Boards'))

            with h.ul(class_="unstyled board-labels"):
                h << [b.render(h, "archived_item")
                      for b in self.archived_boards]

            onclick = 'return confirm("%s")' % _(
                "These boards will be destroyed. Are you sure?")
            h << h.a(_("Delete"), class_="btn btn-primary btn-small",
                     type='submit', onclick=onclick).action(self.purge_archived_boards)
    return h.root
