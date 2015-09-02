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

from nagare import component, log, security
from nagare.i18n import _, _L

from .models import DataCard
from ..checklist import comp as checklist
from ..label import comp as label
from ..comment import comp as comment
from ..vote import comp as vote
from ..description import comp as description
from ..due_date import comp as due_date
from ..title import comp as title
from ..user import usermanager
from .. import exceptions, notifications
from ..toolbox import overlay
from ..gallery import comp as gallery
from nagare import editor
from nagare import validator


# WEIGHTING TYPES
WEIGHTING_OFF = 0
WEIGHTING_FREE = 1
WEIGHTING_LIST = 2


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

    max_shown_members = 3

    def __init__(self, id_, column, assets_manager, data=None):
        """Initialization

        In:
            - ``id_`` -- the id of the card in the database
            - ``column`` -- father
        """
        self.db_id = id_
        self.id = 'card_' + str(self.db_id)
        self.column = column
        self.assets_manager = assets_manager
        self._data = data
        self.reload(data if data else self.data)

    @property
    def board(self):
        return self.column.board

    def reload(self, data=None):
        """Refresh the sub components
        """
        data = data if data else self.data
        self.title = component.Component(CardTitle(self))
        self.checklists = component.Component(checklist.Checklists(self))
        self.description = component.Component(CardDescription(self))
        self.due_date = component.Component(due_date.DueDate(self))
        self.gallery = component.Component(gallery.Gallery(self, self.assets_manager))
        self.comments = component.Component(comment.Comments(self, data.comments))
        self.flow = component.Component(CardFlow(self, self.comments, self.gallery))
        self.labels = component.Component(label.CardLabels(self))
        self.votes = component.Component(vote.Votes(self))
        self.author = component.Component(usermanager.get_app_user(data.author.username, data=data.author))

        self._weight = component.Component(CardWeightEditor(self))

        # members part of the card
        self.overlay_add_members = component.Component(
            overlay.Overlay(lambda r: '+',
                            lambda r: component.Component(self).render(r, model='add_member_overlay'), dynamic=True, cls='card-overlay'))
        self.new_member = component.Component(usermanager.AddMembers(self.autocomplete_method)).on_answer(self.add_members)
        self.members = [component.Component(usermanager.get_app_user(member.username, data=member))
                        for member in data.members]
        self.see_all_members = component.Component(overlay.Overlay(lambda r: "%s more..." % (len(self.members) - self.max_shown_members),
                                                                   lambda r: component.Component(self).on_answer(self.remove_member).render(r, model='members_list_overlay'),
                                                                   dynamic=False, cls='card-overlay'))

    @property
    def favorites(self):
        """Return favorites users for a given card

        Ask favorites to self.column
        Store favorites in self._favorites to avoid CallbackLookupError

        Return:
            - list of favorites (User instances) wrappend on component
        """
        self._favorites = [component.Component(usermanager.get_app_user(username), "friend").on_answer(self.add_members)
                           for (username, _) in sorted(self.column.favorites.items(), key=lambda e:-e[1])[:5]
                           if username not in [member().username for member in self.members]]
        return self._favorites

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
    def weight(self):
        return self.data.weight

    @weight.setter
    def weight(self, value):
        values = {'from': self.data.weight, 'to': value, 'card': self.data.title}
        notifications.add_history(self.column.board.data, self.data, security.get_user().data, u'card_weight', values)
        self.data.weight = value

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
        self.gallery().delete_assets()
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

    def get_authorized_users(self):
        """Return user's which are authorized to be add on this card

        Return:
            - a set of user (UserData instance)
        """
        return set(self.column.get_authorized_users()) | set(self.column.get_pending_users()) - set(self.data.members)

    def autocomplete_method(self, value):
        """ """
        return [u for u in usermanager.UserManager.search(value) if u in self.get_authorized_users()]

    def get_available_labels(self):
        return self.column.get_available_labels()

    #################
    # Members methods
    #################

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
        return "YAHOO.kansha.reload_cards['%s']();YAHOO.kansha.app.hideOverlay();" % self.id

    def _add_members(self, new_data_members):
        """Add members to a card

        In:
            - ``new_data_members`` -- all UserData instance to attach to card
        Return:
            - list of new DataMembers added
        """
        res = []
        for new_data_member in new_data_members:
            if self.add_member(new_data_member):
                res.append(new_data_member)
            values = {'user_id': new_data_member.username, 'user': new_data_member.fullname, 'card': self.data.title}
            notifications.add_history(self.column.board.data, self.data, security.get_user().data, u'card_add_member', values)
        return res

    def add_member(self, new_data_member):
        """Attach new member to card

        In:
            - ``new_data_member`` -- UserData instance
        Return:
            - the new DataMember added
        """
        data = self.data
        if (new_data_member not in data.members and
                new_data_member in self.get_authorized_users()):
            log.debug('Adding %s to members' % (new_data_member.username,))

            data.members.append(new_data_member)
            self.members.append(component.Component(usermanager.get_app_user(new_data_member.username, data=new_data_member)))
            return new_data_member

    def remove_member(self, username):
        """Remove member username from card member"""
        data_member = usermanager.UserManager().get_by_username(username)
        if data_member:
            log.debug('Removing %s from card %s' % (username, self.id))
            data = self.data
            data.members.remove(data_member)
            for member in self.members:
                if member().username == username:
                    self.members.remove(member)
                    values = {'user_id': member().username, 'user': member().data.fullname, 'card': data.title}
                    notifications.add_history(self.column.board.data, data, security.get_user().data, u'card_remove_member', values)
        else:
            raise exceptions.KanshaException(_("User not found : %s" % username))

    def remove_board_member(self, member):
        """Remove member from board

        Remove member from board. If member is linked to a card, remove it
        from the list of members

        In:
            - ``member`` -- Board Member instance to remove
        """
        self.data.remove_board_member(member)
        self.members = [component.Component(usermanager.get_app_user(m.username, data=m))
                        for m in self.data.members]

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
        return gallery.Asset(self.data.cover, self.assets_manager)

    def remove_cover(self):
        self.data.remove_cover()

    def new_start_from_ajax(self, request, response):
        start = dateutil.parser.parse(request.GET['start']).date()
        self.due_date().set_value(start)


class CardTitle(title.Title):

    """Card title component
    """
    model = DataCard
    field_type = 'input'


class CardDescription(description.Description):

    # We work on wards
    model = DataCard
    type = _L('card')


class CardFlow(object):

    """Flow of comments, pictures, and so on, associated to a card"""

    def __init__(self, card, *source_components):
        """Init method
        In:
          - ``source_components`` -- Components
                                     - on an object inheriting from FlowSource
                                     - having a "flow" view
        """
        self.card = card
        self.source_components = source_components

    @property
    def elements(self):
        res = []
        for s in self.source_components:
            res.extend(s().flow_elements)
        return sorted(res, key=lambda el: getattr(el(), 'creation_date', ''), reverse=True)


class CardWeightEditor(editor.Editor):

    """ Card weight Form
    """

    fields = {'weight'}

    def __init__(self, target, *args):
        """
        In:
         - ``target`` -- Card instance
        """
        super(CardWeightEditor, self).__init__(target, self.fields)
        self.weight.validate(self.validate_weight)

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
