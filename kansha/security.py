# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
from base64 import b64encode, b64decode

from Crypto.Cipher import Blowfish
from Crypto import Random

from peak.rules import when

from nagare.security import form_auth, common
from nagare import security

from .user.usermanager import get_app_user
from .board.comp import Board, BoardTitle, BoardDescription
from .card.comp import Card, CardTitle
from .column.comp import Column, ColumnTitle, CardsCounter
from .label.comp import Label, LabelTitle
from .comment.comp import Comment
from .user.usermanager import UserManager
from .gallery.comp import Gallery

from .board.comp import (BOARD_PRIVATE, BOARD_PUBLIC,
                         COMMENTS_OFF, COMMENTS_PUBLIC, COMMENTS_MEMBERS,
                         VOTES_OFF, VOTES_PUBLIC, VOTES_MEMBERS)


class Unauthorized(Exception):
    pass


class Authentication(form_auth.Authentication):

    KEY = 'a*/-+@45JZWiuet:uietsVLMRS/*-+41"_bépçè€.;'

    def _create_user(self, username):
        if username is not None:
            return get_app_user(username)

    def check_password(self, username, _, password):
        user = UserManager().get_by_username(username)
        if not user or not user.email:
            return False
        return user.check_password(password)

    def denies(self, detail):
        raise Unauthorized()

    def cookie_decode(self, cookie):
        try:
            a_iv, token = cookie.split(':')
            iv = b64decode(a_iv)
            cipher = Blowfish.new(self.KEY, Blowfish.MODE_CBC, iv)
            cookie = cipher.decrypt(b64decode(token)).replace('@','')
        except ValueError:
            return (None, None)

        return super(Authentication, self).cookie_decode(cookie)

    def cookie_encode(self, *ids):
        cookie = super(Authentication, self).cookie_encode(*ids)

        bs = Blowfish.block_size
        iv = Random.new().read(bs)
        cipher = Blowfish.new(self.KEY, Blowfish.MODE_CBC, iv)
        # pad cookie to block size.
        # Cookie is ascii base64 + ':', so we can safely pad with '@'.
        missing_bytes = bs - (len(cookie) % bs)
        cookie += '@' * missing_bytes

        return '%s:%s' % (
            b64encode(iv),
            b64encode(cipher.encrypt(cookie))
        )

        return cookie


class Rules(common.Rules):

    @when(common.Rules.has_permission, "user is None")
    def _(self, user, perm, subject):
        """Default security, if user is not logged return False"""
        return False

    @when(common.Rules.has_permission, "user and perm == 'view' and isinstance(subject, Board)")
    @when(common.Rules.has_permission, "user is None and perm == 'view'  and isinstance(subject, Board)")
    def _(self, user, perm, board):
        """Test if user can see the board."""
        return board.is_public() or (user is not None and board.has_member(user) and not board.archived)

    @when(common.Rules.has_permission, "user and perm == 'manage' and isinstance(subject, Board)")
    def _(self, user, perm, board):
        """Test if users is one of the board's managers"""
        return board.has_manager(user)

    @when(common.Rules.has_permission, "user and perm == 'Add Users' and isinstance(subject, Board)")
    def _(self, user, perm, board):
        """Test if users is one of the board's managers, if he is he can add new user to the board"""
        return board.has_manager(user)

    @when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, Board)")
    def _(self, user, perm, board):
        """Test if users is one of the board's members"""
        return board.has_member(user)

    @when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, BoardDescription)")
    def _(self, user, perm, description):
        """Test if description is editable"""
        return security.has_permissions('edit', description.parent)

    @when(common.Rules.has_permission, "user and perm == 'vote' and isinstance(subject, Board)")
    def _(self, user, perm, board):
        return ((board.has_member(user) and board.votes_allowed == VOTES_MEMBERS)
                or ((board.votes_allowed == VOTES_PUBLIC) and user))

    @when(common.Rules.has_permission, "user and perm == 'comment' and isinstance(subject, Board)")
    def _(self, user, perm, board):
        return ((board.has_member(user) and board.comments_allowed == COMMENTS_MEMBERS)
                or ((board.comments_allowed == COMMENTS_PUBLIC) and user))

    @when(common.Rules.has_permission, "user and perm == 'due_date' and isinstance(subject, Board)")
    def _(self, user, perm, board):
        return board.has_member(user) and user

    @when(common.Rules.has_permission, "user and perm == 'checklist' and isinstance(subject, Board)")
    def _(self, user, perm, board):
        return board.has_member(user) and user

    @when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, Gallery)")
    def _(self, user, perm, gallery):
        """Test if description is editable"""
        return security.has_permissions('edit', gallery.card)

    @when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, Column)")
    def _(self, user, perm, column):
        return security.has_permissions('edit', column.board)

    @when(common.Rules.has_permission, "user and perm == 'vote' and isinstance(subject, Column)")
    def _(self, user, perm, column):
        return security.has_permissions('vote', column.board)

    @when(common.Rules.has_permission, "user and perm == 'comment' and isinstance(subject, Column)")
    def _(self, user, perm, column):
        return security.has_permissions('comment', column.board)

    @when(common.Rules.has_permission, "user and perm == 'due_date' and isinstance(subject, Column)")
    def _(self, user, perm, column):
        return security.has_permissions('due_date', column.board)

    @when(common.Rules.has_permission, "user and perm == 'checklist' and isinstance(subject, Column)")
    def _(self, user, perm, column):
        return security.has_permissions('checklist', column.board)

    @when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, Card)")
    def _(self, user, perm, card):
        return security.has_permissions('edit', card.column)

    @when(common.Rules.has_permission, "user and perm == 'vote' and isinstance(subject, Card)")
    def _(self, user, perm, card):
        return security.has_permissions('vote', card.column)

    @when(common.Rules.has_permission, "user and perm == 'comment' and isinstance(subject, Card)")
    def _(self, user, perm, card):
        return security.has_permissions('comment', card.column)

    @when(common.Rules.has_permission, "user and perm == 'due_date' and isinstance(subject, Card)")
    def _(self, user, perm, card):
        return security.has_permissions('due_date', card.column)

    @when(common.Rules.has_permission, "user and perm == 'checklist' and isinstance(subject, Card)")
    def _(self, user, perm, card):
        return security.has_permissions('checklist', card.column)

    @when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, BoardTitle)")
    @when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, CardTitle)")
    def _(self, user, perm, title):
        """Test if title is editable"""
        return security.has_permissions('edit', title.parent)

    @when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, ColumnTitle)")
    def _(self, user, perm, title):
        """Test if title is editable"""
        if title.parent.is_archive:
            return False
        return security.has_permissions('edit', title.parent)

    @when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, LabelTitle)")
    def _(self, user, perm, title):
        """Test if title is editable"""
        return True

    @when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, Label)")
    def _(self, user, perm, subject):
        return security.has_permissions('edit', subject.board)

    @when(common.Rules.has_permission, "user and (perm == 'create_board')")
    def _(self, user, perm, subject):
        """If user is logged, he is allowed to create a board"""
        return True

    @when(common.Rules.has_permission, "user and (perm == 'delete_comment')")
    def _(self, user, perm, comment):
        return comment.is_author(user)

    @when(common.Rules.has_permission, "user and (perm == 'edit_comment')")
    def _(self, user, perm, comment):
        return comment.is_author(user)

    @when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, CardsCounter)")
    def _(self, user, perm, CardsCounter):
        return security.has_permissions('edit', CardsCounter.column)


class SecurityManager(Authentication, Rules):

    def __init__(self, crypto_key):
        Authentication.__init__(self)
        Rules.__init__(self)
        self.KEY = crypto_key
