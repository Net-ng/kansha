# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
from collections import OrderedDict

from nagare import i18n
from nagare import editor
from nagare.i18n import _
from nagare import security
from nagare import component
from nagare import validator, var

from kansha import notifications
from kansha.menu import MenuEntry
from kansha import title


class BoardConfig(object):

    """Board configuration component"""

    def __init__(self, board):
        """Initialization

        In:
            - ``board`` -- the board object will want to configure
        """
        self.board = board
        self.menu = OrderedDict()
        self.menu['profile'] = MenuEntry(_(u'Profile'), 'icon-profile', BoardProfile)
        if security.has_permissions('manage', self.board):
            self.menu['labels'] = MenuEntry(_(u'Card labels'), 'icon-price-tag', BoardLabels)
            self.menu['weights'] = MenuEntry(_(u'Card weights'), 'icon-meter', BoardWeights)
            self.menu['background'] = MenuEntry(_(u'Background'), 'icon-paint-format', BoardBackground)
        self.selected = None
        self.content = component.Component(None)
        self.select(self.menu.iterkeys().next())

    def select(self, v):
        """Select a configuration menu item

        In:
            - ``v`` -- the id_ of the menu item we want to show
        """
        self.selected = v
        self.content.becomes(self.menu[v].content(self.board))


class BoardLabels(object):

    """Board configuration component for board labels"""

    def __init__(self, board):
        """Initialization

        In:
            - ``board`` -- the board object we are working on
        """
        self.board = board
        self.labels = []
        for label in board.labels:
            t = component.Component(title.EditableTitle(label.get_title))
            t.on_answer(label.set_title)
            l = component.Component(label, model='edit-color')
            self.labels.append((t, l))


class BoardWeights(object):

    """Board configuration component for card weights"""

    def __init__(self, board):
        """Initialization

        In:
            - ``board`` -- the board object we are working on
        """
        self.board = board
        self._weights_editor = component.Component(WeightsSequenceEditor(self))

    @property
    def weights(self):
        return self.board.weights

    @weights.setter
    def weights(self, value):
        self.board.weights = value

    def activate_weighting(self, weighting_type):
        self.board.activate_weighting(weighting_type)


class WeightsSequenceEditor(editor.Editor):

    """Weights Sequence form"""
    fields = {'weights'}

    def __init__(self, target, *args):
        """Initialization

        In:
            - ``board`` -- the board object we are working on
        """
        super(WeightsSequenceEditor, self).__init__(target, self.fields)
        self.weights.validate(self.validate_sequence)
        self.feedback = ''

    def validate_sequence(self, value):
        try:
            res = validator.StringValidator(value, strip=True).not_empty(msg=i18n._("Required field")).to_string()
        except ValueError:
            raise
        if res:
            try:
                weights = res.split(',')
                for weight in weights:
                    res = validator.IntValidator(weight).greater_or_equal_than(0).to_int()
            except ValueError:
                raise ValueError(i18n._('Must be positive integers'))
        return value

    def commit(self):
        self.feedback = ''
        if self.is_validated(self.fields):
            super(WeightsSequenceEditor, self).commit(self.fields)
            self.feedback = i18n._('Sequence saved')
            return True
        return False


class BoardProfile(object):

    """Board configuration component"""

    def __init__(self, board):
        """Initialization

        In:
            - ``board`` -- the board object we are working on
        """
        self.board = board

    def allow_comments(self, v):
        """Changes comments permissions

        3 values allowed (off/member/public)

        In:
            - ``v`` -- an integer (see security.py for values)
        """
        self.board.allow_comments(v)

    def allow_votes(self, v):
        """Changes votes permissions

        3 values allowed (off/member/public)

        In:
            - ``v`` -- an integer (see security.py for values)
        """
        self.board.allow_votes(v)

    def allow_notifications(self, v):
        notifications.allow_notifications(security.get_user(), self.board, v)

    @property
    def notifications_allowed(self):
        return notifications.notifications_allowed(security.get_user(), self.board)

    def set_archive(self, value):
        self.board.show_archive = value


class BoardBackground(object):

    """Configuration component for background customization
    """

    def __init__(self, board):
        """Initialization

        In:
            - ``board`` -- the board object we are working on
        """
        self.board = board
        self.background_position = var.Var(self.board.background_image_position)

    def set_background_position(self):
        self.board.set_background_position(self.background_position())

    def set_background(self, img):
        self.board.set_background_image(img)

    def reset_background(self):
        self.board.set_background_image(None)

    def set_color(self, color):
        self.board.set_title_color(color)

    def reset_color(self):
        self.board.set_title_color('')
