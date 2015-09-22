# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import uuid
import urllib

from elixir import using_options
from elixir import ManyToMany, ManyToOne, OneToMany
from elixir import Field, Unicode, Integer, Boolean, UnicodeText

from kansha.models import Entity
from kansha.user.models import DataUser, DataBoardMember
from nagare.database import session
from sqlalchemy.ext.associationproxy import AssociationProxy


class DataBoard(Entity):
    """Board mapper

     - ``title`` -- board title
     - ``columns`` -- list of board columns
     - ``labels`` -- list of labels for cards
     - ``comments_allowed`` -- who can comment ? (0 nobody, 1 board members only , 2 all application users)
     - ``votes_allowed`` -- who can vote ? (0 nobody, 1 board members only , 2 all application users)
     - ``description`` -- board description
     - ``visibility`` -- board visibility (0 Private, 1 Public)
     - ``members`` -- list of members (simple members and manager)
     - ``managers`` -- list of managers
     - ``uri`` -- board URI (Universally Unique IDentifier)
     - ``last_users`` -- list of last users
     - ``pending`` -- invitations pending for new members (use token)
     - ``archive`` -- display archive column ? (0 false, 1 true)
     - ``archived`` -- is board archived ?
    """
    using_options(tablename='board')
    title = Field(Unicode(255))
    columns = OneToMany('DataColumn', order_by="index",
                        cascade='delete')
    labels = OneToMany('DataLabel', order_by='index')
    comments_allowed = Field(Integer, default=1)
    votes_allowed = Field(Integer, default=1)
    description = Field(UnicodeText, default=u'')
    visibility = Field(Integer, default=0)
    version = Field(Integer, default=0, server_default='0')
    board_members = OneToMany('DataBoardMember')
    members = AssociationProxy('board_members', 'member', creator=lambda member: DataBoardMember(member=member))
    managers = ManyToMany('DataUser', order_by=('fullname', 'email'))
    uri = Field(Unicode(255), index=True, unique=True)
    last_users = ManyToOne('DataUser', order_by=('fullname', 'email'))
    pending = OneToMany('DataToken', order_by='username')
    history = OneToMany('DataHistory')

    background_image = Field(Unicode(255))
    background_position = Field(Unicode(255))
    title_color = Field(Unicode(255))
    archive = Field(Integer, default=0)
    archived = Field(Boolean, default=False)

    weighting_cards = Field(Integer, default=0)
    weights = Field(Unicode(255), default=u'')

    def delete_members(self):
        for member in self.board_members:
            session.delete(member)
        session.flush()

    def delete_history(self):
        for event in self.history:
            session.delete(event)
        session.flush()

    def increase_version(self):
        self.version += 1
        if self.version > 2147483600:
            self.version = 1

    @property
    def url(self):
        return urllib.quote_plus(
            "%s/%s" % (self.title.encode('ascii', 'ignore'), self.uri),
            '/'
        )

    def __init__(self, *args, **kwargs):
        """Initialization.

        Create board and uri of the board
        """
        super(DataBoard, self).__init__(*args, **kwargs)
        self.uri = unicode(uuid.uuid4())

    def label_by_title(self, title):
        """Return a label instance which match with title

        In:
         - ``title`` -- the title of the label to search for
        Return:
         - label instance
        """
        return (l for l in self.labels if l.title == title).next()

    @classmethod
    def get_by_id(cls, id):
        return cls.get(id)

    @classmethod
    def get_by_uri(cls, uri):
        return cls.query.filter_by(uri=uri).first()

    def has_member(self, user):
        """Return True if user is member of the board

        In:
         - ``user`` -- user to test (User instance)
        Return:
         - True if user is member of the board
        """
        return user.data in set(dbm.member for dbm in self.board_members)

    def remove_member(self, board_member):
        board_member.delete()

    def has_manager(self, user):
        """Return True if user is manager of the board

        In:
         - ``user`` -- user to test (User instance)
        Return:
         - True if user is manager of the board
        """
        return user.data in self.managers

    def remove_manager(self, board_member):
        self.remove_member(board_member)
        self.managers.remove(board_member.get_user_data())

    def change_role(self, board_member, new_role):
        if new_role == 'manager':
            self.managers.append(board_member.get_user_data())
        else:
            self.managers.remove(board_member.get_user_data())

    def last_manager(self, member):
        """Return True if member is the last manager of the board"""
        return member.role == 'manager' and len(self.managers) == 1

    def add_member(self, new_member, role='member'):
        """ Add new member to the board

        In:
         - ``new_member`` -- user to add (DataUser instance)
         - ``role`` -- role's member (manager or member)
        """
        self.board_members.append(DataBoardMember(member=new_member.data))

        if role == 'manager':
            self.managers.append(new_member.data)

        session.flush()

    def get_pending_users(self):
        emails = [token.username for token in self.pending]
        return DataUser.query.filter(DataUser.email.in_(emails))

    def set_background_image(self, image):
        self.background_image = image or u''
