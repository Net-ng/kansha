# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import security
from peak.rules import when
from nagare.security import common

from kansha.card.comp import Card
from kansha.board.comp import Board
from kansha.column.comp import Column
from kansha.cardextension import CardExtension
from kansha.board.comp import VOTES_PUBLIC, VOTES_MEMBERS

from .models import DataVote


@when(common.Rules.has_permission, "user and perm == 'vote' and isinstance(subject, Board)")
def has_permission_Board_vote(self, user, perm, board):
    return ((board.has_member(user) and board.votes_allowed == VOTES_MEMBERS)
            or ((board.votes_allowed == VOTES_PUBLIC) and user))


@when(common.Rules.has_permission, "user and perm == 'vote' and isinstance(subject, Column)")
def has_permission_Column_vote(self, user, perm, column):
    return security.has_permissions('vote', column.board)


@when(common.Rules.has_permission, "user and perm == 'vote' and isinstance(subject, Card)")
def has_permission_Card_vote(self, user, perm, card):
    return security.has_permissions('vote', card.column)


class Votes(CardExtension):
    '''Vote component'''

    LOAD_PRIORITY = 70

    def count_votes(self):
        '''Returns number of votes for a card'''
        return DataVote.count_votes(self.card.data)

    def toggle(self):
        '''Add a vote to the current card.

        Remove vote if user has already voted
        '''
        security.check_permissions('vote', self.card)
        user = security.get_user()
        if self.has_voted():
            DataVote.get_vote(self.card.data, user.data).delete()
        else:
            DataVote(card=self.card.data, user=user.data)

    def has_voted(self):
        '''Check if the current user already vote for this card'''
        user = security.get_user()
        return DataVote.has_voted(self.card.data, user.data)
