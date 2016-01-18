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

from kansha.toolbox import overlay
from kansha.services.search import schema
from kansha.cardextension import CardExtension

from .models import DataLabel


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

    def get_color(self):
        return self.data.color

    def set_color(self, v):
        """Change the color of the label

        In:
          - ``v`` -- the color of the label as hex string (ex. '#CECECE')
        """
        self.data.color = v
        self._changed(True)

    def get_title(self):
        return self.data.title

    def set_title(self, title):
        """Set title

        In:
            - ``title`` -- new title
        """
        self.data.title = title

    def add(self, card):
        self.data.add(card.data)

    def remove(self, card):
        self.data.remove(card.data)

    def __eq__(self, other):
        return self.id == other.id


class CardLabels(CardExtension):

    """Card labels component

    This component represents all labels associated with a card
    """

    LOAD_PRIORITY = 10

    def __init__(self, card, action_log, configurator):
        """Initialization

        In:
          - ``card`` -- the card object (Card instance)
        """
        super(CardLabels, self).__init__(card, action_log, configurator)
        self.comp_id = str(random.randint(10000, 100000))
        self._comp = component.Component(self)
        self.overlay = component.Component(overlay.Overlay(lambda r: self._comp.render(r, model="list"),
                                                          lambda r: self._comp.render(r, model='overlay'), dynamic=False, cls='card-edit-form-overlay'))

    @staticmethod
    def get_schema_def():
        return schema.Text('labels')

    def update_document(self, document):
        document.labels = u' '.join(label.get_title() for label in self.labels)

    @property
    def data(self):
        return DataLabel.get_by_card(self.card.data)

    def update(self, other):

        active_labels = set(label.get_title() for label in other.labels)
        for label in self.get_available_labels():
            if label.get_title() in active_labels:
                self.activate(label)

    @property
    def labels(self):
        """Returns the Label instances
        """
        return [Label(label) for label in self.data]

    @property
    def colors(self):
        """Returns the colors of the labels associated with the card
        """
        return (l.get_color() for l in self.labels)

    def get_available_labels(self):
        """Returns the labels available in the card's board
        """
        return self.configurator.labels if self.configurator else []

    def activate(self, label):
        """Adds/removes a label to the current card.

        If the label is already associated with the card,
        remove it. Else add it.

        """
        if label in self.labels:
            label.remove(self.card)
        else:
            label.add(self.card)

    def delete(self):
        for label in self.labels:
            label.remove(self.card)
