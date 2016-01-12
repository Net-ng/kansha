# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import dateutil.parser

from peak.rules import when

from nagare.i18n import _
from nagare import (component, log, security, editor, validator)

from kansha import title
from kansha import events
from kansha import exceptions
from kansha.toolbox import overlay
from kansha.user import usermanager
from kansha.cardextension import CardExtension
from kansha.services.actionlog.messages import render_event

from .models import DataCard


class NewCard(object):

    """New card component
    """

    def __init__(self, column):
        self.column = column
        self.needs_refresh = False

    def toggle_refresh(self):
        self.needs_refresh = not self.needs_refresh


class Card(events.EventHandlerMixIn):

    """Card component
    """

    def __init__(self, id_, column, card_extensions, action_log, services_service, data=None):
        """Initialization

        In:
            - ``id_`` -- the id of the card in the database
            - ``column`` -- father
        """
        self.db_id = id_
        self.id = 'card_' + str(self.db_id)
        self.column = column # still used by extensions, not by the card itself
        self.card_extensions = card_extensions
        self.action_log = action_log.for_card(self)
        self._services = services_service
        self._data = data
        self.extensions = ()
        self.refresh()

    def copy(self, parent, additional_data):
        new_data = self.data.copy(parent.data)
        new_card = self._services(Card, new_data.id, parent, {}, parent.action_log, data=new_data)
        new_card.extensions = [(name, component.Component(extension().copy(new_card, additional_data)))
                               for name, extension in self.extensions]
        return new_card

    def refresh(self):
        """Refresh the sub components
        """
        self.title = component.Component(
            title.EditableTitle(self.get_title)).on_answer(self.set_title)
        self.extensions = [
            (name, component.Component(extension))
            for name, extension in self.card_extensions.items(self, self.action_log, self._services)
        ]

    @property
    def data(self):
        """Return the card object from the database
        """
        if self._data is None:
            self._data = DataCard.get(self.db_id)
        return self._data

    def __getstate__(self):
        self._data = None
        return self.__dict__

    @property
    def archived(self):
        return self.data.archived

    @property
    def index(self):
        return self.data.index

    def set_title(self, title):
        """Set title

        In:
            - ``title`` -- new title
        """
        values = {'from': self.data.title, 'to': title}
        self.action_log.add_history(security.get_user(), u'card_title', values)
        self.data.title = title

    def get_title(self):
        """Get title

        Return :
            - the card title
        """
        return self.data.title

    def delete(self):
        """Prepare for deletion"""
        for __, extension in self.extensions:
            extension().delete()

    def card_dropped(self, request, response):
        """
        Dropped on new date (calendar view).
        """
        start = dateutil.parser.parse(request.GET['start']).date()
        for __, extension in self.extensions:
            extension().new_card_position(start)

    def emit_event(self, comp, kind, data=None):
        if kind == events.PopinClosed:
            kind = events.CardEditorClosed
        return super(Card, self).emit_event(comp, kind, data)

    ################################
    # Feature methods, persistency #
    ################################

    # Members

    def add_member(self, new_data_member):
        self.data.members.append(new_data_member)

    def remove_member(self, data_member):
        self.data.remove_member(data_member)

    @property
    def members(self):
        return self.data.members

    def remove_board_member(self, member):
        """Member removed from board

        If member is linked to a card, remove it
        from the list of members

        In:
            - ``member`` -- Board Member instance to remove
        """
        self.data.remove_member(member.get_user_data())
        self.refresh()  # brute force solution until we have proper communication between extensions

    # Cover methods

    def make_cover(self, asset):
        """Make card cover with asset

        In:
            - ``asset`` -- New cover, Asset component
        """
        self.data.make_cover(asset)

    def has_cover(self):
        return self.data.cover is not None

    def get_cover(self):
        return self.data.cover

    def remove_cover(self):
        self.data.remove_cover()

    # Label methods

    def get_datalabels(self):
        return self.data.labels

    # Weight

    @property
    def weight(self):
        return self.data.weight

    @weight.setter
    def weight(self, value):
        values = {'from': self.data.weight, 'to': value, 'card': self.data.title}
        self.action_log.add_history(security.get_user(), u'card_weight', values)
        self.data.weight = value

    # Comments

    def get_comments(self):
        return self.data.comments

    # Description

    def get_description(self):
        return self.data.description

    def set_description(self, value):
        self.data.description = value

    # Checklists

    def get_datalists(self):
        return self.data.checklists

    # Due Date

    @property
    def due_date(self):
        return self.data.due_date

    @due_date.setter
    def due_date(self, value):
        self.data.due_date = value


############### Extension components ###################


@when(render_event, "action=='card_weight'")
def render_event_card_weight(action, data):
    return _(u'Card "%(card)s" has been weighted from (%(from)s) to (%(to)s)') % data


class CardWeightEditor(editor.Editor, CardExtension):

    """ Card weight Form
    """

    LOAD_PRIORITY = 80

    fields = {'weight'}
    # WEIGHTING TYPES
    WEIGHTING_OFF = 0
    WEIGHTING_FREE = 1
    WEIGHTING_LIST = 2

    def __init__(self, target, action_log, configurator):
        """
        In:
         - ``target`` -- Card instance
        """
        editor.Editor.__init__(self, target, self.fields)
        CardExtension.__init__(self, target, action_log, configurator)
        self.weight.validate(self.validate_weight)
        self.action_button = component.Component(self, 'action_button')

    def validate_weight(self, value):
        """
        Integer or empty
        """
        if value:
            validator.IntValidator(value).to_int()
        return value

    @property
    def weighting_switch(self):
        return self.configurator.weighting_cards if self.configurator else self.WEIGHTING_OFF

    @property
    def allowed_weights(self):
        return self.configurator.weights if self.configurator else ''

    def commit(self):
        success = False
        if self.is_validated(self.fields):
            super(CardWeightEditor, self).commit(self.fields)
            success = True
        return success

##


@when(render_event, "action=='card_add_member'")
def render_event_card_add_member(action, data):
    return _(u'User %(user)s has been assigned to card "%(card)s"') % data


@when(render_event, "action=='card_remove_member'")
def render_event_card_remove_member(action, data):
    return _(u'User %(user)s has been unassigned from card "%(card)s"') % data


class CardMembers(CardExtension):

    LOAD_PRIORITY = 90

    max_shown_members = 3

    def __init__(self, card, action_log, configurator):
        """
        Card is a card business object.
        """

        super(CardMembers, self).__init__(card, action_log, configurator)

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
        available_user_ids = self.get_available_user_ids()
        return [u for u in usermanager.UserManager.search(value) if u.id in available_user_ids]

    def get_available_user_ids(self):
        """Return user's which are authorized to be added on this card

        Return:
            - a set of user (UserData instance)
        """
        return self.get_all_available_user_ids() | self.get_pending_user_ids() - set(user.id for user in self.card.members)

    def get_all_available_user_ids(self):
        return self.configurator.get_available_user_ids() if self.configurator else []

    def get_pending_user_ids(self):
        return self.configurator.get_pending_user_ids() if self.configurator else []

    @property
    def member_stats(self):
        return self.configurator.get_member_stats() if self.configurator else {}

    @property
    def favorites(self):
        """Return favorites users for a given card

        Return:
            - list of favorites (User instances) wrappend on component
        """

        # to be optimized later if still exists
        member_usernames = set(member.username for member in self.card.members)
        # FIXME: don't reference parent
        board_user_stats = [(nb_cards, username) for username, nb_cards in self.member_stats.iteritems()]
        board_user_stats.sort(reverse=True)
        # Take the 5 most popular that are not already affected to this card
        favorites = [username for (__, username) in board_user_stats
                     if username not in member_usernames]

        self._favorites = [component.Component(usermanager.UserManager.get_app_user(username), "friend")
                           for username in favorites[:5]]
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
        if (new_data_member not in self.card.members and
            new_data_member.id in self.get_available_user_ids()):

            self.card.add_member(new_data_member)
            log.debug('Adding %s to members' % (new_data_member.username,))
            self.members.append(
                component.Component(usermanager.UserManager.get_app_user(
                    new_data_member.username, data=new_data_member)))

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
