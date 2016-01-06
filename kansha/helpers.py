#-*- coding: utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

#=-
# (C)opyright PagesJaunes 2011
#
# This is Pagesjaunes proprietary source code
# Any reproduction modification or use without prior written
# approval from PagesJaunes is strictly forbidden.
#=-
import random
import string
from datetime import datetime, timedelta

from nagare import local, security
from nagare.database import session

from kansha.user import usermanager
from kansha.board import boardsmanager
from kansha.security import SecurityManager
from kansha.card.models import DataCard
from kansha.card_addons.vote import DataVote
from kansha.board import models as board_models
from kansha.services.mail import DummyMailSender
from kansha.services.search.dummyengine import DummySearchEngine
from kansha.services.services_repository import ServicesRepository
from kansha.services.dummyassetsmanager.dummyassetsmanager import DummyAssetsManager


def setup_db(metadata):
    """Setup the tables

    In:
        - ``metadata`` -- the metadata from models
    """
    metadata.create_all()


def teardown_db(metadata):
    """Drop the tables

    In:
        - ``metadata`` -- the metadata from models
    """
    metadata.drop_all()
    session.close()


def word(length=20):
    """Random string generator

    In:
        - ``length`` -- the length of the string
    """
    return u''.join(random.sample(string.ascii_letters, length))


def integer():
    """Random integer generator
    """
    return random.randint(1, 10000)


class DummySecurityManager(security.common.Rules):

    """
    Dummy Security Manager to be used in unit tests
    """

    def has_permission(self, user, perm, subject):
        return True


def set_dummy_context():
    """Set a dummy context for security permission checks
    """
    local.request = local.Thread()
    security.set_user(None)
    security.set_manager(DummySecurityManager())


def set_context(user=None):
    """ """
    local.request = local.Thread()
    security.set_user(user)
    security.set_manager(SecurityManager('somekey'))


def get_or_create_data_user(suffixe=''):
    '''Get test user for suffixe, or create if not exists'''
    user_test = usermanager.UserManager.get_by_username(
        u'usertest_%s' % suffixe)
    if not user_test:
        user_test = usermanager.UserManager().create_user(
            u'usertest_%s' % suffixe,
            u'password', u'User Test %s' % suffixe,
            u'user_test%s@net-ng.com' % suffixe)
        session.add(user_test)
    return user_test


def create_user(suffixe=''):
    """Create Test user
    """
    user_test = get_or_create_data_user(suffixe)
    return usermanager.UserManager.get_app_user(u'usertest_%s' % suffixe)


def create_services():
    'Service mockups for testing components'
    _services = ServicesRepository()
    _services.register('assets_manager', DummyAssetsManager())
    _services.register('mail_sender', DummyMailSender())
    return _services


def create_board():
    """Create boards with default columns and default cards
    """
    user = create_user()
    services = create_services()
    boards_manager = boardsmanager.BoardsManager('', '', '', {}, DummySearchEngine(None), services)
    template = board_models.create_template_todo()
    template = boards_manager.get_by_id(template.id)
    board = boards_manager.copy_board(template, user, False)
    create_default_cards(board.data, user)
    user.add_board(board, "manager")
    board.set_title(word())
    board.load_data()
    return board


def create_default_cards(board, user):
    user = user.data
    green = board.get_label_by_title(u'Green')
    red = board.get_label_by_title(u'Red')
    column_1 = board.columns[0]
    cards = [DataCard(title=u"Welcome to your board!", creation_date=datetime.utcnow(), due_date=datetime.utcnow() + timedelta(5)),
             DataCard(title=u"We've created some lists and cards for you, so you can play with it right now!", creation_date=datetime.utcnow()),
             DataCard(title=u"Use color-coded labels for organization",
                      labels=[green, red], creation_date=datetime.utcnow()),
             DataCard(title=u"Make as many lists as you need!",
                      votes=[DataVote(user=user)], creation_date=datetime.utcnow()),
             DataCard(title=u"Try dragging cards anywhere.", creation_date=datetime.utcnow()),
             DataCard(title=u"Finished with a card? Delete it.", creation_date=datetime.utcnow(), due_date=datetime.utcnow() + timedelta(-2)),
             ]
    for i, c in enumerate(cards):
        c.index = i
    column_1.cards = cards
    column_1.nb_max_cards = len(cards)

    column_2 = board.columns[1]
    cards = [DataCard(title=u'This is a card.', creation_date=datetime.utcnow()),
             DataCard(title=u"Click on a card to see what's behind it.", creation_date=datetime.utcnow()),
             DataCard(title=u"You can add files to a card.", creation_date=datetime.utcnow()),
             DataCard(
                 title=u'To learn more tricks, check out the manual.', creation_date=datetime.utcnow()),
             DataCard(title=u"Use as many boards as you want.", creation_date=datetime.utcnow())]
    for i, c in enumerate(cards):
        c.index = i
    column_2.cards = cards
    column_2.nb_max_cards = len(cards) + 2
    session.refresh(board)
