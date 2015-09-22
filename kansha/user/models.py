# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import datetime
import string
import random
import hashlib

from elixir import using_options
from elixir import ManyToOne, ManyToMany, OneToOne, OneToMany
from elixir import Unicode, Integer, Field, DateTime, Boolean
from sqlalchemy.dialects.mysql import VARCHAR
from nagare import database
from sqlalchemy import and_, func
from sqlalchemy.orm import aliased
from sqlalchemy.ext.associationproxy import AssociationProxy

from kansha.models import Entity


class DataBoardMember(Entity):
    using_options(tablename='user_boards__board_members')
    board = ManyToOne('DataBoard', primary_key=True, ondelete='CASCADE')
    member = ManyToOne('DataUser', primary_key=True, ondelete='CASCADE', colname=[
                       'user_username', 'user_source'])
    notify = Field(Integer, default=lambda: 1)


class DataUser(Entity):

    """Label mapper
    """
    using_options(tablename='user')
    # VARCHAR(binary=True) here is a hack to make MySQL case sensitive
    # like the other DBMS.
    # No consequences on regular databases.
    username = Field(
        VARCHAR(255, binary=True), unique=True,
        primary_key=True, nullable=False)
    source = Field(Unicode(255), nullable=False, primary_key=True)
    fullname = Field(Unicode(255), nullable=False)
    email = Field(Unicode(255), nullable=True)
    picture = Field(Unicode(255), nullable=True)
    language = Field(Unicode(255), default=u"en", nullable=True)
    email_to_confirm = Field(Unicode(255))
    _salt = Field(Unicode(255), colname='salt', nullable=False)
    _password = Field(Unicode(255), colname='password', nullable=True)
    registration_date = Field(DateTime, nullable=False)
    last_login = Field(DateTime, nullable=True)
    display_week_numbers = Field(Boolean, default=False)
    board_members = OneToMany('DataBoardMember')
    boards = AssociationProxy(
        'board_members', 'board',
        creator=lambda board: DataBoardMember(board=board))
    managed_boards = ManyToMany('DataBoard', inverse='managers')
    last_board = OneToOne('DataBoard', inverse='last_users')
    cards = ManyToMany('DataCard', inverse='members', lazy='dynamic')
    my_cards = OneToMany('DataCard', inverse='author')
    history = OneToMany('DataHistory')
    votes = OneToMany('DataVote')

    def __init__(self, username, password, fullname, email,
                 source=u'application', picture=None, **kw):
        """Create a new user with an unconfirmed email"""
        super(DataUser, self).__init__(username=username,
                                       fullname=fullname,
                                       email=None,
                                       email_to_confirm=email,
                                       source=source,
                                       picture=picture,
                                       registration_date=datetime.datetime.utcnow(), **kw)
        # Create password if source is local
        if source == "application":
            self.change_password(password)
        else:
            # External authentication
            self.change_password('passwd')
            self.email_to_confirm = None

    def update(self, fullname, email, picture=None):
        self.fullname = fullname
        if email:
            self.email = email
        self.picture = picture

    def check_password(self, clear_password):
        """Check the user password. Return True if the password is valid for this user"""
        encrypted_password = self._encrypt_password(self._salt, clear_password)
        return encrypted_password == self._password

    def change_password(self, clear_password):
        """Change the user password"""
        self._salt = self._create_random_salt()
        self._password = self._encrypt_password(self._salt, clear_password)

    def set_email_to_confirm(self, email_to_confirm):
        if email_to_confirm:
            self.email_to_confirm = email_to_confirm


    def is_validated(self):
        return self.email_to_confirm is None

    def confirm_email(self):
        """Called when a user confirms his email address"""
        # already confirmed
        if self.email_to_confirm is None:
            return

        self.email = self.email_to_confirm
        self.email_to_confirm = None

    def add_board(self, board, role="member"):
        """Add board to user's board lists

        In:
         - ``board`` -- DataBoard instance to add
         - ``role`` -- user is member or manager
        """
        boards = set(dbm.board for dbm in self.board_members)
        if board not in boards:
            self.board_members.append(DataBoardMember(board=board))
        if role == "manager" and board not in self.managed_boards:
            self.managed_boards.append(board)

    def get_picture(self):
        if self.picture is None:
            return "img/member.png"
        else:
            return self.picture

    @classmethod
    def get_confirmed_users(cls):
        return cls.query.filter(cls.email is not None)

    @staticmethod
    def _create_random_salt(length=32):
        allowed_chars = string.ascii_letters + string.digits
        return u''.join(random.choice(allowed_chars) for _ in range(length))

    @staticmethod
    def _encrypt_password(salt, password):
        secret = "NzlSszmvDNY2e2lVMwiKJwgWjNGFCP1a"
        secret_salt = hashlib.sha512(secret + salt).hexdigest()
        utf8_password = password.encode('utf-8')
        return unicode(hashlib.sha512(secret_salt + utf8_password).hexdigest())

    @classmethod
    def get_unconfirmed_users(cls, before_date=None):
        q = cls.query.filter(cls.email is None)
        if before_date:
            q = q.filter(cls.registration_date < before_date)
        return q

    @classmethod
    def get_by_username(cls, username):
        return cls.get_by(username=username)

    @classmethod
    def get_by_email(cls, email):
        return cls.get_by(email=email)

    @classmethod
    def search(cls, value):
        return cls.query.filter(cls.fullname.ilike('%' + value + '%') | cls.email.ilike('%' + value + '%'))

    def best_friends(self, exclude_list=(), size=None):
        from kansha.board.models import DataBoard

        cls = self.__class__
        bm2 = aliased(DataBoardMember)
        cnt = func.count(DataBoardMember.board_id)
        query = database.session.query(cls, cnt)
        query = query.join((DataBoardMember, and_(DataBoardMember.user_source == cls.source,
                                                  DataBoardMember.user_username == cls.username)))
        query = query.join(
            (DataBoard, DataBoard.id == DataBoardMember.board_id))
        query = query.join((bm2, bm2.board_id == DataBoard.id))
        query = query.filter(bm2.member == self)
        if exclude_list:
            query = query.filter(~cls.email.in_(exclude_list))
        query = query.group_by(cls)
        query = query.order_by(cnt.desc(), cls.fullname)
        if size:
            query = query.limit(size)
        return [res[0] for res in query]
