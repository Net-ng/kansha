# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import os
import sys

from nagare import local, log, security

from kansha.security import SecurityManager
from kansha.services.dummyassetsmanager.dummyassetsmanager import DummyAssetsManager
from kansha.services.services_repository import ServicesRepository
from kansha.services.mail import DummyMailSender

from .board.boardsmanager import BoardsManager
from .user import usermanager


def populate():
    """Populate database
    """
    local.request = local.Thread()
    security.set_manager(SecurityManager(''))

    services = ServicesRepository()
    services.register('assets_manager', DummyAssetsManager())
    services.register('mail_sender', DummyMailSender())

    boards_manager = BoardsManager('', '', '', {}, None, services)
    boards_manager.create_template_empty()
    boards_manager.create_template_todo()
    usermanager.UserManager().populate()
