# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
from datetime import datetime, timedelta, date
from glob import glob
import os.path
import json
import time

from nagare import database

from .models import DataBoard
from ..label.models import DataLabel
from ..card.models import DataCard
from ..card.fts_schema import Card as FTSCard
from ..column.models import DataColumn
from ..comment.models import DataComment
from ..vote.models import DataVote


DEFAULT_LABELS = (
    (u'Green', u'#22C328'),
    (u'Red', u'#CC3333'),
    (u'Blue', u'#3366CC'),
    (u'Yellow', u'#D7D742'),
    (u'Orange', u'#DD9A3C'),
    (u'Purple', u'#8C28BD')
)


class BoardsManager(object):

    def create_board(self, title, user, default=False):
        """Create new board

        In:
            - ``title`` -- a string, board title
            - ``user`` -- owner of the board (UserData instance)
            - ``default`` -- a boolean, create default card on board ?
        Return:
            - new DataBoard created
        """
        board = DataBoard(title=title)
        self.create_default_columns(board)
        self.create_default_label(board)
        if default:
            self.create_default_cards(board, user)
        user.add_board(board, "manager")
        return board

    def get_by_id(self, id):
        return DataBoard.get(id)

    def get_by_uri(self, uri):
        return DataBoard.get_by_uri(uri)

    def create_default_columns(self, board):
        """Create three default columns for new board

        In:
          - ``board`` -- the new board
        """
        for title, index in [(u'To Do', 0), (u'Doing', 1), (u'Done', 2)]:
            DataColumn(title=title, index=index, board=board)

    def create_default_label(self, board):
        for i, (title, color) in enumerate(DEFAULT_LABELS):
            DataLabel(title=title, color=color, board=board, index=i)

    def create_default_cards(self, board, user):
        green = board.label_by_title(u'Green')
        red = board.label_by_title(u'Red')
        column_1 = board.columns[0]
        cards = [DataCard(title=u"Welcome to your board!", author=user, creation_date=datetime.utcnow(), due_date=datetime.utcnow() + timedelta(5)),
                 DataCard(title=u"We've created some lists and cards for you, so you can play with it right now!", author=user, creation_date=datetime.utcnow()),
                 DataCard(title=u"Use color-coded labels for organization",
                          labels=[green, red], author=user, creation_date=datetime.utcnow()),
                 DataCard(title=u"Make as many lists as you need!",
                          votes=[DataVote(user=user)], author=user, creation_date=datetime.utcnow()),
                 DataCard(title=u"Try dragging cards anywhere.", author=user, creation_date=datetime.utcnow()),
                 DataCard(title=u"Finished with a card? Delete it.", author=user, creation_date=datetime.utcnow(), due_date=datetime.utcnow() + timedelta(-2)),
                 ]
        for i, c in enumerate(cards):
            c.index = i
        column_1.cards = cards
        column_1.nb_max_cards = len(cards)

        column_2 = board.columns[1]
        cards = [DataCard(title=u'This is a card.', author=user, creation_date=datetime.utcnow()),
                 DataCard(title=u"Click on a card to see what's behind it.", author=user, creation_date=datetime.utcnow()),
                 DataCard(title=u"You can add files to a card.", author=user, creation_date=datetime.utcnow()),
                 DataCard(
                     title=u'To learn more tricks, check out the manual.', author=user, creation_date=datetime.utcnow()),
                 DataCard(title=u"Use as many boards as you want.", author=user, creation_date=datetime.utcnow())]
        for i, c in enumerate(cards):
            c.index = i
        column_2.cards = cards
        column_2.nb_max_cards = len(cards) + 2

    @staticmethod
    def index_user_cards(user, search_engine):
        for card in user.my_cards:
            search_engine.add_document(FTSCard.from_model(card))
        search_engine.commit()

    @staticmethod
    def create_boards_from_templates(user, folder):
        '''user is a DataUser'''
        for tplf_name in glob(os.path.join(folder, '*.btpl')):
            tpl = json.loads(open(tplf_name).read())
            board = DataBoard(title=tpl['title'])
            labels_def = tpl.get('tags', DEFAULT_LABELS)
            for i, (title, color) in enumerate(labels_def):
                __ = DataLabel(title=title,
                               color=color,
                               index=i,
                               board=board)
            database.session.flush()
            for i, col in enumerate(tpl.get('columns', [])):
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
                                    author=user,
                                    due_date=due_date,
                                    creation_date=datetime.utcnow(),
                                    column=col,
                                    index=j,
                                    labels=[board.labels[i] for i in labels])
                    for comment in comments:
                        comment = DataComment(comment=comment,
                                              author=user,
                                              creation_date=datetime.utcnow(),
                                              card=card)
            board.members.append(user)
            board.managers.append(user)
            database.session.flush()
