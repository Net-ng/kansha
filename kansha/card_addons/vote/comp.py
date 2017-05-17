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

from kansha.card import Card
from kansha.cardextension import CardExtension
from kansha.board import VOTES_PUBLIC, VOTES_MEMBERS

from .models import DataVote


class Votes(CardExtension):
    '''Vote component'''

    LOAD_PRIORITY = 70

    @property
    def allowed(self):
        return self.configurator.votes_allowed

    def count_votes(self):
        '''Returns number of votes for a card'''
        return DataVote.count_votes(self.card.data)

    def toggle(self):
        '''Add a vote to the current card.

        Remove vote if user has already voted
        '''
        security.check_permissions('vote', self)
        user = security.get_user()
        if self.has_voted():
            DataVote.get_vote(self.card.data, user.data).delete()
        else:
            DataVote.new(card=self.card.data, user=user.data)

    def has_voted(self):
        '''Check if the current user already vote for this card'''
        user = security.get_user()
        return DataVote.has_voted(self.card.data, user.data)

    def delete(self):
        DataVote.purge(self.card.data)


# FIXME: redesign security from scratch
@when(common.Rules.has_permission, "user and perm == 'vote' and isinstance(subject, Votes)")
def has_permission_Card_vote(self, user, perm, votes):
    return ((security.has_permissions('edit', votes.card) and votes.allowed == VOTES_MEMBERS) or
            (votes.allowed == VOTES_PUBLIC and user))
