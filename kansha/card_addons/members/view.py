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

from .comp import CardMembers


@presentation.render_for(CardMembers, 'action')
def render_card_members(self, h, comp, model):
    """Member section view for card

    First members icons,
    Then icon "more user" if necessary
    And at the end icon "add user"
    """
    if not security.has_permissions('edit', self.card):
        return h.root
    with h.div(class_='members'):
        h << h.script('''YAHOO.kansha.app.hideOverlay();''')
        for m in self.members[:self.MAX_SHOWN_MEMBERS]:
            h << m.on_answer(self.remove_member).render(h, model="overlay-remove")
        if len(self.members) > self.MAX_SHOWN_MEMBERS:
            h << h.div(self.see_all_members, class_='more')
        h << h.div(self.overlay_add_members, class_='add')
    return h.root


@presentation.render_for(CardMembers, 'badge')
@presentation.render_for(CardMembers, model='members_read_only')
def render_card_members_read_only(self, h, comp, model):
    """Member section view for card

    First members icons,
    Then icon "more user" if necessary
    And at the end icon "add user"
    """
    with h.div(class_='members'):
        for m in self.members[:self.MAX_SHOWN_MEMBERS]:
            h << h.span(m.render(h, 'avatar'), class_='miniavatar unselectable')
        if len(self.members) > self.MAX_SHOWN_MEMBERS:
            if model == 'badge':
                h << comp.render(h, 'more_users')
            else:
                h << h.div(self.see_all_members, class_='more')
    return h.root


@presentation.render_for(CardMembers, 'members_list_overlay')
def render_members_members_list_overlay(self, h, comp, *args):
    """Overlay to list all members"""
    h << h.h2(_('All members'))
    # with h.form:
    with h.div(class_="members"):
        if security.has_permissions('edit', self.card):
            h << [m.on_answer(comp.answer).render(h, "remove") for m in self.members]
        else:
            h << [m.render(h, "avatar") for m in self.members]
    return h.root


def _add_members(member_ext, members):
    member_ext.add_members(members)
    return "YAHOO.kansha.reload_cards['%s']();YAHOO.kansha.app.hideOverlay();" % member_ext.card.id


@presentation.render_for(CardMembers, 'add_member_overlay')
def render_members_add_member_overlay(self, h, comp, *args):
    """Overlay to add member"""
    h << h.h2(_('Add members'))
    favorites = self.favorites
    if favorites:
        with h.div(class_='favorites'):
            h << h.h3(_('Suggestions'))
            with h.ul:
                for favorite in favorites:
                    h << h.li(favorite.on_answer(lambda members: _add_members(self, members)))
    with h.div(class_='members search'):
        h << self.new_member.on_answer(lambda members: _add_members(self, members))
    return h.root


@presentation.render_for(CardMembers, 'more_users')
def render_members_many_user(self, h, comp, *args):
    number = len(self.members) - self.MAX_SHOWN_MEMBERS
    return h.span(
        h.i(class_='ico-btn icon-user'),
        h.span(number, class_='count'),
        title=_('%s more...') % number)
