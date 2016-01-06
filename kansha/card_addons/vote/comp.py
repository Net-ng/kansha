# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import database, security

from kansha.cardextension import CardExtension

from .models import DataVote


class Votes(CardExtension):
    '''Vote component'''

    LOAD_PRIORITY = 70

    def count_votes(self):
        '''Returns number of votes for a card'''
        return DataVote.count_votes(self.card.data)

    def vote(self):
        '''Add a vote to the current card.

        Remove vote if user has already voted
        '''
        security.check_permissions('vote', self.card)
        if not self.has_voted():
            user = security.get_user()
            vote = DataVote(user=user.data)
            self.votes.append(vote)
        else:
            self.unvote()

    def unvote(self):
        '''Remove a vote to the current card'''
        security.check_permissions('vote', self.card)
        if self.has_voted():
            user = security.get_user()
            vote = DataVote.get_vote(self.card.data, user.data)
            self.votes.remove(vote)

    def __nonzero__(self):
        '''Check whether there are votes on the current card or not'''
        return self.count_votes() > 0

    def has_voted(self):
        '''Check if the current user already vote for this card'''
        user = security.get_user()
        return DataVote.has_voted(self.card.data, user.data)
