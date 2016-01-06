#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.i18n import _
from nagare import component, security

from kansha import exceptions
from kansha.toolbox import overlay
from kansha.user import usermanager
from kansha.cardextension import CardExtension


class CardMembers(CardExtension):

    LOAD_PRIORITY = 90

    max_shown_members = 3

    def __init__(self, card, action_log):
        """
        Card is a card business object.
        """

        super(CardMembers, self).__init__(card, action_log)

        # members part of the card
        self.overlay_add_members = component.Component(
            overlay.Overlay(lambda r: (r.i(class_='ico-btn icon-user'), r.span(_(u'+'), class_='count')),
                            lambda r: component.Component(self).render(r, model='add_member_overlay'), dynamic=True, cls='card-overlay'))
        self.new_member = component.Component(usermanager.NewMember(self.autocomplete_method), model='add_members')
        self.members = [component.Component(usermanager.UserManager.get_app_user(member.username, data=member))
                        for member in card.members]

        self.see_all_members = component.Component(
            overlay.Overlay(lambda r: component.Component(self).render(r, model='more_users'),
                            lambda r: component.Component(self).on_answer(self.remove_member).render(r, model='members_list_overlay'),
                            dynamic=False, cls='card-overlay'))

    def autocomplete_method(self, value):
        """ """
        return [u for u in usermanager.UserManager.search(value) if u in self.card.get_available_users()]

    @property
    def favorites(self):
        """Return favorites users for a given card

        Return:
            - list of favorites (User instances) wrappend on component
        """
        self._favorites = [component.Component(usermanager.UserManager.get_app_user(username), "friend")
                           for username in self.card.favorites]
        return self._favorites

    def add_members(self, emails):
        """Add new members from emails

        In:
            - ``emails`` -- emails in string separated by "," or list of strings
        Return:
            - JS code, reload card and hide overlay
        """
        members = []
        # Get all users with emails
        members = filter(None, map(usermanager.UserManager.get_by_email, emails))
        for new_data_member in members:
            self.add_member(new_data_member)
            values = {'user_id': new_data_member.username, 'user': new_data_member.fullname, 'card': self.card.get_title()}
            self.action_log.add_history(security.get_user(), u'card_add_member', values)

    def add_member(self, new_data_member):
        """Attach new member to card

        In:
            - ``new_data_member`` -- UserData instance
        Return:
            - the new DataMember added
        """
        if self.card.add_member(new_data_member):
            log.debug('Adding %s to members' % (new_data_member.username,))
            self.members.append(component.Component(usermanager.UserManager.get_app_user(new_data_member.username, data=new_data_member)))

    def remove_member(self, username):
        """Remove member username from card member"""
        data_member = usermanager.UserManager.get_by_username(username)
        if not data_member:
            raise exceptions.KanshaException(_("User not found : %s" % username))

        log.debug('Removing %s from card %s' % (username, self.card.id))
        self.card.remove_member(data_member)
        for member in self.members:
            if member().username == username:
                self.members.remove(member)
                values = {'user_id': member().username, 'user': member().data.fullname, 'card': self.card.get_title()}
                self.action_log.add_history(security.get_user(), u'card_remove_member', values)
