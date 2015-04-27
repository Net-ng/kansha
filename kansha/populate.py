# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from .user import usermanager
from nagare import log
import sys
import os


def populate():
    """Populate database
    """
    usermanager.UserManager().populate()

    app_path = 'kansha'
    nagare_admin = os.path.join(os.path.dirname(sys.executable), 'nagare-admin')
    batch_file = os.path.join(app_path, 'batch', 'populate_demo_images.py')
    log.info('Run ``%s batch %s %s`` if you want to create demo images.' % (nagare_admin, app_path, batch_file))
