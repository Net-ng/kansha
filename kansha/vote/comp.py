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

    LOAD_PRIORITY = 70

    """Vote component
    """

    @property
    def votes(self):
        card_data = self.card.data
        return card_data.votes

    def vote(self):
        """Add a vote to the current card.

        Remove vote if user has already voted
        """
        security.check_permissions('vote', self.card)
        if not self.has_voted():
            user = security.get_user()
            card_data = self.card.data  # Garbage collector pbm with ORM
            vote = DataVote(user=user.data)
            self.votes.append(vote)
        else:
            self.unvote()

    def unvote(self):
        """Remove a vote to the current card
        """
        security.check_permissions('vote', self.card)
        if self.has_voted():
            user = security.get_user()
            card_data = self.card.data
            vote = DataVote.get_vote(user.data, card_data)
            self.votes.remove(vote)

    def __nonzero__(self):
        """Check whether there are votes on the current card or not
        """
        return bool(self.votes)

    def has_voted(self):
        """Check if the current user already vote for this card
        """
        user = security.get_user()
        q = database.session.query(DataVote)
        q = q.filter(DataVote.user == user.data)
        card_data = self.card.data
        q = q.filter(DataVote.card == card_data)
        return q.count() > 0
