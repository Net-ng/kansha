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
import json
import time
from glob import glob
from datetime import date, datetime

from nagare import database

from kansha.user.models import DataUser
from kansha.card.models import DataCard
from kansha.board.models import DataBoard
from kansha.column.models import DataColumn
from kansha.card_addons.label import DataLabel
from kansha.card_addons.comment import DataComment


DEFAULT_LABELS = (
    (u'Vert', u'#22C328'),
    (u'Rouge', u'#CC3333'),
    (u'Bleu', u'#3366CC'),
    (u'Jaune', u'#D7D742'),
    (u'Orange', u'#DD9A3C'),
    (u'Violet', u'#8C28BD')
)


def create_boards_from_templates(user, folder):
    for template_filename in glob(os.path.join(folder, '*.btpl')):
        template = json.loads(open(template_filename).read())
        board = DataBoard(title=template['title'])
        labels_def = template.get('tags', DEFAULT_LABELS)
        for i, (title, color) in enumerate(labels_def):
            __ = DataLabel(title=title,
                           color=color,
                           index=i,
                           board=board)
        database.session.flush()
        for i, col in enumerate(template.get('columns', [])):
            cards = col.pop('cards', [])
            col = DataColumn(title=col['title'],
                             index=i,
                             board=board)
            for j, card in enumerate(cards):
                comments = card.pop('comments', [])
                labels = card.pop('tags', [])
                due_date = card.pop('due_date', None)
                if due_date:
                    due_date = time.strptime(due_date, '%Y-%m-%d')
                    due_date = date(*due_date[:3])
                card = DataCard(title=card['title'],
                                description=card.get('description', u''),
                                due_date=due_date,
                                creation_date=datetime.utcnow(),
                                column=col,
                                index=j,
                                labels=[board.labels[i] for i in labels])
                for comment in comments:
                    DataComment(comment=comment,
                                author=user,
                                creation_date=datetime.utcnow(),
                                card=card)
        board.members.append(user)
        board.managers.append(user)
        database.session.flush()


if len(sys.argv) != 3:
    print 'Usage: %s email template_folder' % sys.argv[0]

user = DataUser.get_by_email(sys.argv[1])
if not user:
    print 'No such user, exiting.'
    sys.exit(0)

folder = sys.argv[2]
create_boards_from_templates(user, folder)
database.session.commit()
