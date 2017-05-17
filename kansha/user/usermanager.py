# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
import random
from datetime import datetime, timedelta

from nagare.namespaces import xhtml
from nagare import component, i18n

from .comp import User
from .models import DataUser
from kansha.toolbox import autocomplete


class UserManager(object):

    @classmethod
    def get_app_user(cls, username=None, data=None):
        """Return User instance"""
        if not data:
            data = cls.get_by_username(username)
        else:
            username = data.username
        if data.source != 'application':
            # we need to set a passwd for nagare auth
            user = User(username, 'passwd', data=data)
        else:
            user = User(username, data=data)
        return user

    @staticmethod
    def search(value):
        """Return all users which name begins by value"""
        return DataUser.search(value)

    @staticmethod
    def get_all_users(hours=0):
        """Return all data users if `hours` is 0 or just those who have registrated
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
                    source=u'application', picture=None):
        from kansha.authentication.database import forms
        user = DataUser(username, password, fullname, email,
                        source, picture, language=i18n.get_locale().language)
        token_gen = forms.TokenGenerator(email, u'invite board')
        for token in token_gen.get_tokens():
            if token_gen.check_token(token.token) and token.board:
                token.board.add_member(user)
            token_gen.reset_token(token.token)
        return user


###### TODO: Move the defintions below somewhere else ##########

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
        # FIXME: dont access data attributes!
        h = xhtml.Renderer(static_url=static_url)
        return [(u.email or u.email_to_confirm, component.Component(UserManager.get_app_user(data=u)).render(h, "search").write_htmlstring())
                for u in self.autocomplete_method(value)]


# class AddMembers(NewMember):

#     pass
