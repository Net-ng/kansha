# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation, security
from nagare.i18n import _, _N

from .comp import Votes


@presentation.render_for(Votes, model='edit')
def render_Votes_edit(self, h, comp, *args):
    """Add vote form"""
    if security.has_permissions('vote', self.parent):
        nb_votes = len(self.votes)
        if self.has_voted():
            h << h.a(h.i(class_='icon-heart icon-grey'), _('Unvote (%s)') % nb_votes,
                     class_='btn btn-small').action(self.vote)
        else:
            h << h.a(h.i(class_='icon-heart icon-grey'), _('Vote (%s)') % nb_votes,
                     class_='btn btn-small').action(self.vote)
    return h.root


@presentation.render_for(Votes, model='badge')
def render_Votes_badge(self, h, *args):
    """Badge for card in summary view

    User can vote by clicking on the icon
    """
    if self.votes:
        label = _N('vote', 'votes', len(self.votes))
        label = u'%s %s' % (len(self.votes), label)
        id_ = h.generate_id()
        link = h.a(h.i(class_='icon-heart icon-grey'), ' ', len(self.votes), class_='label', id=id_, data_tooltip=label)
        # Test if user can vote
        if security.has_permissions('vote', self.parent):
            link.action(self.vote)
        h << link
        h << h.script("YAHOO.util.Event.addListener('%s', 'click', YAHOO.util.Event.stopPropagation); " % id_)

    return h.root
