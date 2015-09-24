# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from .models import DataUser
from nagare.namespaces import xhtml
from nagare import component, i18n
from ..toolbox import autocomplete
import random
from datetime import datetime, timedelta


def get_user_class(source):
    """ Return User Class for a given source

    Generic method (from peak). Authentication system implements this
    method.

    In:
     - ``source`` -- login source (i.e application, google...)
    Return:
     - the user class
    """
    raise Exception("User class for source %s not found" % source)


def get_app_user(username, data=None):
    """Return User instance"""
    if not data:
        data = UserManager().get_by_username(username)
    klass = get_user_class(data.source)
    return klass(username, data=data)


class UserManager(object):

    @staticmethod
    def search(value):
        """Return all users which name begins by value"""
        return DataUser.search(value)

    @staticmethod
    def get_all_users(hours=0):
        """Return all users if `hours` is 0 or just those who have registrated
        for the last hours."""
        q = DataUser.query
        if hours:
            since = datetime.utcnow() - timedelta(hours=hours)
            q = q.filter(DataUser.registration_date >= since)
        return q.all()

    @staticmethod
    def get_by_username(username):
        return DataUser.get_by_username(username)

    @staticmethod
    def get_by_email(email):
        return DataUser.get_by_email(email)

    @staticmethod
    def get_unconfirmed_users(before_date):
        """Return unconfirmed user

        Return all user which have'nt email validated before a date
        In:
            - ``before_date`` -- limit date
        Return:
            - list of DataUser instance
        """
        return DataUser.get_unconfirmed_users(before_date)

    @staticmethod
    def get_confirmed_users():
        """Return confirmed user

        Return all user which have email validated

        Return:
            - list of DataUser instance
        """
        return DataUser.get_confirmed_users()

    def create_user(self, username, password, fullname, email,
                    source=u'application', picture=None, create_board=True):
        from ..authentication.database import forms
        from ..board.boardsmanager import BoardsManager
        user = DataUser(username, password, fullname, email,
                        source, picture, language=i18n.get_locale().language)
        token_gen = forms.TokenGenerator(email, u'invite board')
        for token in token_gen.get_tokens():
            if token_gen.check_token(token.token) and token.board:
                user.add_board(token.board)
            token_gen.reset_token(token.token)
        if create_board:
            BoardsManager().create_board(u"Welcome Board", user, True)
        return user

    def populate(self):
        user1 = self.create_user(
            u'user1', u'password', u'user 1', u'user1@net-ng.com')
        user1.confirm_email()

        user2 = self.create_user(
            u'user2', u'password', u'user 2', u'user2@net-ng.com')
        user2.confirm_email()

        user3 = self.create_user(
            u'user3', u'password', u'user 3', u'user3@net-ng.com')
        user3.confirm_email()

        user1.boards[0].title = u"Welcome Board User1"
        user2.boards[0].title = u"Welcome Board User2"
        user3.boards[0].title = u"Welcome Board User3"

        # Share boards and cards for tests
        user1.boards[0].members.extend([user2, user3])
        user2.boards[0].members.append(user1)
        user1.boards[0].columns[0].cards[3].members = [user1, user2]
        user1.boards[0].columns[1].cards[2].members = [user1, user2, user3]
        user1.boards[0].columns[1].cards[1].members = [user3]
        user2.boards[0].columns[0].cards[1].members = [user1, user2]

        # Add comment from other user
        for u1, u2 in ((user1, user2),
                       (user2, user3),
                       (user3, user1)):
            from ..comment.models import DataComment
            u1.boards[0].columns[0].cards[-1].comments.append(DataComment(comment=u"I agree.",
                                                                          creation_date=datetime.utcnow(),
                                                                          author=u2))


class NewMember(object):

    """New Member Class"""

    def __init__(self, autocomplete_method):
        """Init method

        In:
            - ``autocomplete_methode`` -- method called for autocomplete
        """
        self.text_id = 'new_members_' + str(random.randint(10000000, 99999999))
        self.autocomplete = component.Component(
            autocomplete.Autocomplete(self.text_id, self.autocompletion, delimiter=','))
        self.autocomplete_method = autocomplete_method

    def autocompletion(self, value, static_url):
        """Return users with email which match with value.

        Method called by autocomplete. This method returns a list of tuples.
        First element of tuple is the email's user. The second is a HTML
        fragment to display in the list of matches.

        In:
         - ``value`` -- first letters of user email
        Return:
         - list of tuple (email, HTML string)
        """
        h = xhtml.Renderer(static_url=static_url)
        return [(u.email, component.Component(get_app_user(u.username, data=u)).render(h, "search").write_htmlstring())
                for u in self.autocomplete_method(value)]


class AddMembers(object):

    def __init__(self, autocomplete_method):
        self.text_id = 'add_members_' + str(random.randint(10000000, 99999999))
        self.autocomplete = component.Component(
            autocomplete.Autocomplete(self.text_id, self.autocompletion, delimiter=','))
        self.autocomplete_method = autocomplete_method

    def autocompletion(self, value, static_url):
        h = xhtml.Renderer(static_url=static_url)
        return [(u.email, component.Component(get_app_user(u.username, data=u)).render(h, "search").write_htmlstring()) for u in self.autocomplete_method(value)]
