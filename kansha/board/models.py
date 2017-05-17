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
from elixir import ManyToOne, OneToMany, OneToOne
from elixir import Field, Unicode, Integer, Boolean, UnicodeText

from kansha.models import Entity
from nagare.database import session
from kansha.user.models import DataUser
from kansha.column.models import DataColumn
# provisional until we have board extensions
from kansha.card_addons.label import DataLabel
# provisional until we have board extensions
from kansha.card_addons.weight import DataBoardWeightConfig
# provisional until we have board extensions
from kansha.card_addons.members.models import DataMembership

# Board visibility
BOARD_PRIVATE = 0
BOARD_PUBLIC = 1
BOARD_SHARED = 2


class DataBoard(Entity):
    """Board mapper

     - ``title`` -- board title
     - ``is_template`` -- is this a real board or a template?
     - ``columns`` -- list of board columns
     - ``labels`` -- list of labels for cards
     - ``comments_allowed`` -- who can comment ? (0 nobody, 1 board members only , 2 all application users)
     - ``votes_allowed`` -- who can vote ? (0 nobody, 1 board members only , 2 all application users)
     - ``description`` -- board description
     - ``visibility`` -- board visibility [0 Private, 1 Public (anyone with the URL can view),
                                           2 Shared (anyone can view it from her home page)]
     - ``uri`` -- board URI (Universally Unique IDentifier)
     - ``last_users`` -- list of last users
     - ``pending`` -- invitations pending for new members (use token)
     - ``archive`` -- display archive column ? (0 false, 1 true)
     - ``archived`` -- is board archived ?
    """
    using_options(tablename='board')
    title = Field(Unicode(255))
    is_template = Field(Boolean, default=False)
    columns = OneToMany('DataColumn', order_by="index",
                        cascade='delete', lazy='subquery')
    # provisional
    labels = OneToMany('DataLabel', order_by='index')
    comments_allowed = Field(Integer, default=1)
    votes_allowed = Field(Integer, default=1)
    description = Field(UnicodeText, default=u'')
    visibility = Field(Integer, default=0)
    version = Field(Integer, default=0, server_default='0')
    # provisional
    board_members = OneToMany('DataMembership', lazy='subquery', order_by=('manager'))
    uri = Field(Unicode(255), index=True, unique=True)
    last_users = ManyToOne('DataUser', order_by=('fullname', 'email'))
    pending = OneToMany('DataToken', order_by='username')
    history = OneToMany('DataHistory')

    background_image = Field(Unicode(255))
    background_position = Field(Unicode(255))
    title_color = Field(Unicode(255))
    show_archive = Field(Integer, default=0)
    archived = Field(Boolean, default=False)

    # provisional
    weight_config = OneToOne('DataBoardWeightConfig')

    def __init__(self, *args, **kwargs):
        """Initialization.

        Create board and uri of the board
        """
        super(DataBoard, self).__init__(*args, **kwargs)
        self.uri = unicode(uuid.uuid4())

    @property
    def template_title(self):
        manager = self.get_first_manager()
        if not manager or self.visibility == 0:
            return self.title
        return u'{0} ({1})'.format(self.title, manager.fullname)

    def get_first_manager(self):
        if not self.board_members:
            return None
        potential_manager = self.board_members[-1]
        return potential_manager.user if potential_manager.manager else None

    def copy(self):
        new_data = DataBoard(title=self.title,
                             description=self.description,
                             background_position=self.background_position,
                             title_color=self.title_color,
                             comments_allowed=self.comments_allowed,
                             votes_allowed=self.votes_allowed)
        # TODO: move to board extension
        new_data.weight_config = DataBoardWeightConfig(
            weighting_cards=self.weighting_cards,
            weights=self.weights)
        session.add(new_data)
        session.flush()
        # TODO: move to board extension
        for label in self.labels:
            new_data.labels.append(label.copy())
        session.flush()
        return new_data

    def get_label_by_title(self, title):
        return (l for l in self.labels if l.title == title).next()

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
        return "%s/%s" % (urllib.quote_plus(self.title.encode('ascii', 'ignore').replace('/', '_')), self.uri)

    @classmethod
    def get_by_id(cls, id):
        return cls.get(id)

    @classmethod
    def get_by_uri(cls, uri):
        return cls.get_by(uri=uri)

    def set_background_image(self, image):
        self.background_image = image or u''

    @classmethod
    def get_all_boards(cls, user):
        """Return all boards the user is member of."""
        query = session.query(cls).join(DataMembership)
        query = query.filter(cls.is_template == False, DataMembership.user == user)
        return query.order_by(cls.title)

    @classmethod
    def get_shared_boards(cls):
        query = session.query(cls).filter(cls.visibility == BOARD_SHARED)
        return query.order_by(cls.title)

    @classmethod
    def get_templates_for(cls, user, public_value):
        q = cls.query
        q = q.filter(cls.archived == False)
        q = q.filter(cls.is_template == True)
        q = q.order_by(cls.title)

        q1 = q.filter(cls.visibility == public_value)

        q2 = q.join(DataMembership)
        q2 = q2.filter(DataMembership.user == user)
        q2 = q2.filter(cls.visibility != public_value)

        return q1, q2

    def create_column(self, index, title, nb_cards=None, archive=False):
        return DataColumn.create_column(self, index, title, nb_cards, archive)

    def delete_column(self, column):
        if column in self.columns:
            self.columns.remove(column)

    def create_label(self, title, color):
        label = DataLabel(title=title, color=color)
        self.labels.append(label)
        session.flush()
        return label

    ############# Membership management; those functions belong to a board extension

    def delete_members(self):
        DataMembership.delete_members(self)

    def has_member(self, user):
        """Return True if user is member of the board

        In:
         - ``user`` -- user to test (DataUser instance)
        Return:
         - True if user is member of the board
        """
        return DataMembership.has_member(self, user)

    def has_manager(self, user):
        """Return True if user is manager of the board

        In:
         - ``user`` -- user to test (DataUser instance)
        Return:
         - True if user is manager of the board
        """
        return DataMembership.has_member(self, user, manager=True)

    def remove_member(self, user):
        DataMembership.remove_member(board=self, user=user)

    def change_role(self, user, new_role):
        DataMembership.change_role(self, user, new_role == 'manager')

    def add_member(self, user, role='member'):
        """ Add new member to the board

        In:
         - ``new_member`` -- user to add (DataUser instance)
         - ``role`` -- role's member (manager or member)
        """
        DataMembership.add_member(self, user, role == 'manager')

    ############# Weight configuration, those functions belong to an extension

    @property
    def weights(self):
        return self.weight_config.weights

    @weights.setter
    def weights(self, value):
        self.weight_config.weights = value

    @property
    def weighting_cards(self):
        return self.weight_config.weighting_cards

    @weighting_cards.setter
    def weighting_cards(self, value):
        self.weight_config.weighting_cards = value

    def reset_card_weights(self):
        self.weight_config.reset_card_weights()

    def total_weight(self):
        return self.weight_config.total_weight()

# Populate
DEFAULT_LABELS = (
    (u'Green', u'#22C328'),
    (u'Red', u'#CC3333'),
    (u'Blue', u'#3366CC'),
    (u'Yellow', u'#D7D742'),
    (u'Orange', u'#DD9A3C'),
    (u'Purple', u'#8C28BD')
)


def create_template_empty():
    board = DataBoard(title=u'Empty board', is_template=True, visibility=1)
    board.weight_config = DataBoardWeightConfig()
    for title, color in DEFAULT_LABELS:
        board.create_label(title=title, color=color)
    session.flush()
    return board


def create_template_todo():
    board = DataBoard(title=u'Basic Kanban', is_template=True, visibility=1)
    board.weight_config = DataBoardWeightConfig()
    for index, title in enumerate((u'To Do', u'Doing', u'Done')):
        board.create_column(index, title)
    for title, color in DEFAULT_LABELS:
        board.create_label(title=title, color=color)
    session.flush()
    return board
