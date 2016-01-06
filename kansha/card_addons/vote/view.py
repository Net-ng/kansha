# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.i18n import _
from nagare import presentation, security

from .comp import Votes


@presentation.render_for(Votes, model='action')
def render_Votes_edit(self, h, comp, *args):
    '''Add vote form'''
    if security.has_permissions('vote', self.card):
        nb_votes = self.count_votes()
        if self.has_voted():
            h << h.a(h.i(class_='icon-heart'), _('Unvote (%s)') % nb_votes,
                     class_='btn').action(self.vote)
        else:
            h << h.a(h.i(class_='icon-heart'), _('Vote (%s)') % nb_votes,
                     class_='btn').action(self.vote)
    return h.root


@presentation.render_for(Votes, model='badge')
def render_Votes_badge(self, h, *args):
    '''Badge for card in summary view'''
    nb_votes = self.count_votes()
    if nb_votes:
        with h.span(class_='badge'):
            h << h.span(h.i(class_='icon-heart'), ' ', nb_votes, class_='label')
    return h.root
