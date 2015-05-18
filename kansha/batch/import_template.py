#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
import sys

from nagare import database
from kansha.user.models import DataUser
from kansha.board.boardsmanager import BoardsManager


DEFAULT_LABELS = (
    (u'Vert', u'#22C328'),
    (u'Rouge', u'#CC3333'),
    (u'Bleu', u'#3366CC'),
    (u'Jaune', u'#D7D742'),
    (u'Orange', u'#DD9A3C'),
    (u'Violet', u'#8C28BD')
)

if len(sys.argv) != 3:
    print 'Usage: %s email template_folder' % sys.argv[0]

user = DataUser.get_by_email(sys.argv[1])
if not user:
    print 'No such user, exiting.'
    sys.exit(0)

folder = sys.argv[2]
BoardsManager.create_boards_from_templates(user, folder)
database.session.commit()
