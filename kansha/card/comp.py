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

from nagare import (component, log, security, editor, validator)
from nagare.i18n import _

from kansha import exceptions, notifications
from kansha.checklist import comp as checklist
from kansha.comment import comp as comment
from kansha.description import comp as description
from kansha.due_date import comp as due_date
from kansha.gallery import comp as gallery
from kansha.label import comp as label
from kansha.title import comp as title
from kansha.toolbox import overlay
from kansha.user import usermanager
from kansha.vote import comp as vote
from kansha.services.components_repository import CardExtension

from .models import DataCard


class NewCard(object):

    """New card component
    """

    def __init__(self, column):
        self.column = column
        self.needs_refresh = False

    def toggle_refresh(self):
        self.needs_refresh = not self.needs_refresh


class Card(object):

    """Card component
    """

    def __init__(self, id_, column, services_service, data=None):
        """Initialization

        In:
            - ``id_`` -- the id of the card in the database
            - ``column`` -- father
        """
        self.db_id = id_
        self.id = 'card_' + str(self.db_id)
        self.column = column
        self._services = services_service
        self._data = data
        self.card_extensions = tuple()
        self.reload(data if data else self.data)

    @property
    def must_reload_search(self):
        return self.board.must_reload_search

    def reload_search(self):
        return self.board.reload_search()

    @property
    def board(self):
        return self.column.board

    def reload(self, data=None):
        """Refresh the sub components
        """
        EXTENSIONS_CLASSES = (
            ('labels', label.CardLabels),
            ('description', description.CardDescription),
            ('checklists', checklist.Checklists),
            ('gallery', gallery.Gallery),
            ('comments', comment.Comments),
            ('due_date', due_date.DueDate),
            ('votes', vote.Votes),
            ('_weight', CardWeightEditor),
            ('card_members', CardMembers)
        )
        self.title = component.Component(CardTitle(self))
        self.card_extensions = [(name, component.Component(self._services(extension, self)))
                                for name, extension in EXTENSIONS_CLASSES]

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

    def set_title(self, title):
        """Set title

        In:
            - ``title`` -- new title
        """
        values = {'from': self.data.title, 'to': title}
        notifications.add_history(self.column.board.data, self.data, security.get_user().data, u'card_title', values)
        self.data.title = title

    def get_title(self):
        """Get title

        Return :
            - the card title
        """
        return self.data.title

    def delete(self):
        """Delete itself"""
        for __, extension in self.card_extensions:
            extension().delete()
        DataCard.delete_card(self.data)

    def move_card(self, card_index, column):
        """Move card

        In:
            - ``card_index`` -- new index of the card
            - ``column`` -- new father
        """
        data_card = self.data
        data_card.index = card_index
        column.data.cards.append(data_card)
        self.column = column

    def card_dropped(self, request, response):
        """
        Dropped on new date (calendar view).
        """
        start = dateutil.parser.parse(request.GET['start']).date()
        for __, extension in self.card_extensions:
            extension().new_card_position(start)

    ################################
    # Feature methods, persistency #
    ################################

    # Members

    def get_authorized_users(self):
        """Return user's which are authorized to be add on this card

        Return:
            - a set of user (UserData instance)
        """
        return set(self.column.get_authorized_users()) | set(self.column.get_pending_users()) - set(self.data.members)

    def add_member(self, new_data_member):
        data = self.data
        added = False
        if (new_data_member not in data.members and
                new_data_member in self.get_authorized_users()):
            data.members.append(new_data_member)
            added = True
        return added

    def remove_member(self, data_member):
        data = self.data
        data.members.remove(data_member)

    @property
    def members(self):
        return self.data.members

    @property
    def favorites(self):
        """Return favorites users for a given card

        Ask favorites to self.column
        Store favorites in self._favorites to avoid CallbackLookupError

        Return:
            - list of favorites (usernames)
        """
        # to be optimized later if still exists
        self._favorites = [username
                           for (username, _) in sorted(self.column.favorites.items(), key=lambda e:-e[1])[:5]
                           if username not in [member.username for member in self.members]]
        return self._favorites

    def remove_board_member(self, member):
        """Member removed from board

        If member is linked to a card, remove it
        from the list of members

        In:
            - ``member`` -- Board Member instance to remove
        """
        self.data.remove_board_member(member)
        self.reload()  # brute force solution until we have proper communication between extensions

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

    def get_available_labels(self):
        return self.column.get_available_labels()

    def get_datalabels(self):
        return self.data.labels

    # Weight

    @property
    def weight(self):
        return self.data.weight

    @weight.setter
    def weight(self, value):
        values = {'from': self.data.weight, 'to': value, 'card': self.data.title}
        notifications.add_history(self.column.board.data, self.data, security.get_user().data, u'card_weight', values)
        self.data.weight = value

    def weighting_on(self):
        return self.board.weighting_cards

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

class CardTitle(title.Title):

    """Card title component
    """
    model = DataCard
    field_type = 'input'


class CardWeightEditor(editor.Editor, CardExtension):

    """ Card weight Form
    """

    fields = {'weight'}
    # WEIGHTING TYPES
    WEIGHTING_OFF = 0
    WEIGHTING_FREE = 1
    WEIGHTING_LIST = 2

    def __init__(self, target, *args):
        """
        In:
         - ``target`` -- Card instance
        """
        super(CardWeightEditor, self).__init__(target, self.fields)
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
    def board(self):
        return self.target.board

    def commit(self):
        if self.is_validated(self.fields):
            super(CardWeightEditor, self).commit(self.fields)
            return True
        return False


class CardMembers(CardExtension):

    max_shown_members = 3

    def __init__(self, card):
        """
        Card is a card business object.
        """

        self.card = card

        # members part of the card
        self.overlay_add_members = component.Component(
            overlay.Overlay(lambda r: r.i(class_='ico-btn icon-user-plus'),
                            lambda r: component.Component(self).render(r, model='add_member_overlay'), dynamic=True, cls='card-overlay'))
        self.new_member = component.Component(usermanager.NewMember(self.autocomplete_method), model='add_members').on_answer(self.add_members)
        self.members = [component.Component(usermanager.UserManager.get_app_user(member.username, data=member))
                        for member in card.members]

        self.see_all_members = component.Component(overlay.Overlay(lambda r: self.many_user_render(r, len(card.members) - self.max_shown_members),
                                                                   lambda r: component.Component(self).on_answer(self.remove_member).render(r, model='members_list_overlay'),
                                                                   dynamic=False, cls='card-overlay'))

    def autocomplete_method(self, value):
        """ """
        return [u for u in usermanager.UserManager.search(value) if u in self.card.get_authorized_users()]

    @staticmethod
    def many_user_render(h, number):
        return h.span(
            h.i(class_='ico-btn icon-user-nb'),
            h.span(number, class_='count'),
            title=_("%s more...") % number)

    @property
    def favorites(self):
        """Return favorites users for a given card

        Return:
            - list of favorites (User instances) wrappend on component
        """
        self._favorites = [component.Component(usermanager.UserManager.get_app_user(username), "friend").on_answer(self.add_members)
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
        if isinstance(emails, (str, unicode)):
            emails = [e.strip() for e in emails.split(',') if e.strip() != '']
        # Get all users with emails
        for email in emails:
            new_member = usermanager.UserManager.get_by_email(email)
            if new_member:
                members.append(new_member)
        self._add_members(members)
        return "YAHOO.kansha.reload_cards['%s']();YAHOO.kansha.app.hideOverlay();" % self.card.id

    def _add_members(self, new_data_members):
        """Add members to a card

        In:
            - ``new_data_members`` -- all UserData instance to attach to card
        Return:
            - list of new DataMembers added
        """
        for new_data_member in new_data_members:
            self.add_member(new_data_member)
            #values = {'user_id': new_data_member.username, 'user': new_data_member.fullname, 'card': self.data.title}
            #notifications.add_history(self.column.board.data, self.data, security.get_user().data, u'card_add_member', values)

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
        if data_member:
            log.debug('Removing %s from card %s' % (username, self.card.id))
            self.card.remove_member(data_member)
            for member in self.members:
                if member().username == username:
                    self.members.remove(member)
                    #values = {'user_id': member().username, 'user': member().data.fullname, 'card': data.title}
                    #notifications.add_history(self.column.board.data, data, security.get_user().data, u'card_remove_member', values)
        else:
            raise exceptions.KanshaException(_("User not found : %s" % username))
