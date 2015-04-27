# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import random

from nagare import component, var

from .models import DataLabel
from ..toolbox import overlay
from ..title import comp as title


class Label(object):

    """Label component

    6 labels by board
    A label contains tuple (color, title)
    """

    def __init__(self, data):
        """Initialization

        In:
          - ``data`` -- the label's database object
        """
        self.id = data.id
        self._changed = var.Var(False)

    @property
    def data(self):
        """Return the label from the database

        Return:
         - the DataLabel instance
        """
        return DataLabel.get(self.id)

    def set_color(self, v):
        """Change the color of the label

        In:
          - ``v`` -- the color of the label as hex string (ex. '#CECECE')
        """
        self.data.color = v
        self._changed(True)

    def set_title(self, title):
        """Set title

        In:
            - ``title`` -- new title
        """
        self.data.title = title

    def get_title(self):
        """Get title

        Return :
            - the board title
        """
        return self.data.title


class CardLabels(object):

    """Card labels component

    This component represents all labels associated with a card
    """

    def __init__(self, card):
        """Initialization

        In:
          - ``card`` -- the card object (Card instance)
        """
        self.card = card
        self.comp_id = str(random.randint(10000, 100000))
        self.labels = [l.id for l in card.data.labels]
        self._comp = component.Component(self)
        self.overlay = component.Component(overlay.Overlay(lambda r: self._comp.render(r, model="list"),
                                                           lambda r: self._comp.render(r, model='overlay'), dynamic=False, cls='card-edit-form-overlay'))

    @property
    def data_labels(self):
        """Returns the DataLabel instances
        """
        return [DataLabel.get(label_id) for label_id in self.labels]

    @property
    def colors(self):
        """Returns the colors of the labels associated with the card
        """
        return (l.color for l in self.data_labels)

    def get_available_labels(self):
        """Returns the labels available in the card's board
        """
        return self.card.get_available_labels()

    def activate(self, label_id):
        """Adds/removes a label to the current card.

        If the label is already associated with the card,
        remove it. Else add it.

        In:
            - ``label_id`` -- the id of the label to add/remove.
        """
        card = self.card.data
        if label_id in self.labels:
            card.labels = [l for l in card.labels if l.id != label_id]
            self.labels.pop(self.labels.index(label_id))
        else:
            card.labels.append(DataLabel.get(label_id))
            self.labels.append(label_id)
            self.labels.sort()


class LabelTitle(title.Title):

    """Label title component
    """
    field_type = 'input'
