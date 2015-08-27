# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import component, security, var
from nagare.i18n import _

from kansha import notifications
from ..label import comp as label
from nagare import editor
from nagare import validator
from nagare import i18n


class BoardConfig(object):

    """Board configuration component"""

    def __init__(self, board):
        """Initialization

        In:
            - ``board`` -- the board object will want to configure
        """
        self.board = board
        self.menu = [(_(u'Profile'), BoardProfile)]
        if security.has_permissions('manage', self.board):
            self.menu.append((_(u'Card labels'), BoardLabels))
            self.menu.append((_(u'Card weights'), BoardWeights))
            self.menu.append((_(u'Background'), BoardBackground))
        self.selected = None
        self.content = component.Component(None)
        self.select(self.menu[0][0])

    def select(self, v):
        """Select a configuration menu item

        In:
            - ``v`` -- the label of the menu item we want to show
        """
        for label, o in self.menu:
            if label == v:
                self.content.becomes(o(self.board))
                self.selected = v
                break


class BoardLabels(object):

    """Board configuration component for board labels"""

    def __init__(self, board):
        """Initialization

        In:
            - ``board`` -- the board object we are working on
        """
        self.board = board
        self.labels = []
        for data in board.labels:
            new_label = label.Label(data)
            t = component.Component(label.LabelTitle(new_label))
            l = component.Component(new_label, model='edit-color')
            self.labels.append((t, l))


class BoardWeights(object):

    """Board configuration component for card weights"""

    def __init__(self, board):
        """Initialization

        In:
            - ``board`` -- the board object we are working on
        """
        self.board = board
        self._changed = var.Var(False)
        self._weights_editor = component.Component(WeightsSequenceEditor(self))

    @property
    def weights(self):
        return self.board.weights

    @weights.setter
    def weights(self, value):
        self.board.weights = value

    def activate_weighting(self, weighting_type):
        self.board.activate_weighting(weighting_type)
        self._changed(True)

    def deactivate_weighting(self):
        self.board.deactivate_weighting()
        self._changed(True)


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

    def validate_sequence(self, value):
        try:
            res = validator.StringValidator(value, strip=True).not_empty(msg=i18n._("Required field")).to_string()
        except:
            raise
        if res:
            try:
                weights = res.split(',')
                for weight in weights:
                    res = validator.IntValidator(weight).to_int()
            except:
                raise ValueError(i18n._('Must be composed of integers'))
        return value

    def commit(self):
        if self.is_validated(self.fields):
            super(WeightsSequenceEditor, self).commit(self.fields)
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
        self._changed = var.Var(False)

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
        self.board.set_archive(value)
        self._changed(True)


class BoardBackground(object):

    """Configuration component for background customization
    """

    def __init__(self, board):
        """Initialization

        In:
            - ``board`` -- the board object we are working on
        """
        self.board = board
        self._changed = var.Var(False)
