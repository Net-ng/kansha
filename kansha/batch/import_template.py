#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--


import datetime
import time
import json
import sys

from nagare import database
from kansha.user.models import DataUser
from kansha.board.models import DataBoard
from kansha.column.models import DataColumn
from kansha.card.models import DataCard
from kansha.comment.models import DataComment
from kansha.label.models import DataLabel


DEFAULT_LABELS = (
    (u'Vert', u'#22C328'),
    (u'Rouge', u'#CC3333'),
    (u'Bleu', u'#3366CC'),
    (u'Jaune', u'#D7D742'),
    (u'Orange', u'#DD9A3C'),
    (u'Violet', u'#8C28BD')
)

if len(sys.argv) != 3:
    print 'Usage: %s email template' % sys.argv[0]

user = DataUser.get_by_email(sys.argv[1])
if not user:
    print 'No such user, exiting.'
    sys.exit(0)
try:
    with open(sys.argv[2], 'r') as f:
        tpl = json.loads(f.read())
except:
    print 'Invalid file, exiting.'
    sys.exit(0)

board = DataBoard(title=tpl['title'])
for i, (title, color) in enumerate(DEFAULT_LABELS):
    label = DataLabel(title=title,
                      color=color,
                      index=i,
                      board=board)
database.session.flush()
for i, col in enumerate(tpl.get('columns', [])):
    cards = col.pop('cards', [])
    col = DataColumn(title=col['title'],
                     index=i,
                     board=board)
    for card in cards:
        comments = card.pop('comments', [])
        labels = card.pop('tags', [])
        due_date = card.pop('due_date', None)
        if due_date:
            due_date = time.strptime(due_date, '%Y-%m-%d')
            due_date = datetime.date(*due_date[:3])
        card = DataCard(title=card['title'],
                        description=card.get('description', u''),
                        author=user,
                        due_date=due_date,
                        creation_date=datetime.datetime.utcnow(),
                        column=col,
                        labels=[board.labels[i] for i in labels])
        for comment in comments:
            comment = DataComment(comment=comment,
                                  author=user,
                                  creation_date=datetime.datetime.utcnow(),
                                  card=card)
board.members.append(user)
board.managers.append(user)
database.session.flush()
database.session.commit()
