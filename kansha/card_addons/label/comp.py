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

    def copy(self, parent, additional_data):
        new_data = self.data.copy(parent.data)
        return Label(new_data)

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
        self.labels = [l.id for l in self.data]
        self._comp = component.Component(self)
        self.overlay = component.Component(overlay.Overlay(lambda r: self._comp.render(r, model="list"),
                                                          lambda r: self._comp.render(r, model='overlay'), dynamic=False, cls='card-edit-form-overlay'))

    @staticmethod
    def get_schema_def():
        return schema.Text('labels')

    def to_indexable(self):
        return u' '.join(label.title for label in self.data_labels)

    @property
    def data(self):
        return DataLabel.get_by_card(self.card.data)

    def copy(self, parent, additional_data):
        new_extension = super(CardLabels, self).copy(parent, additional_data)
        new_labels = dict(((label.data.color, label.data.title), label.id) for label in additional_data['labels'])
        for label in self.data_labels:
            label_id = new_labels.get((label.color, label.title))
            if label_id is not None:
                new_extension.activate(label_id)
        del new_labels
        return new_extension


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
        return self.configurator.labels if self.configurator else []

    def activate(self, label_id):
        """Adds/removes a label to the current card.

        If the label is already associated with the card,
        remove it. Else add it.

        In:
            - ``label_id`` -- the id of the label to add/remove.
        """
        card = self.card.data
        if label_id in self.labels:
            DataLabel.remove_from_card(card, label_id)
            self.labels = [l.id for l in DataLabel.get_by_card(card)]
        else:
            self.labels.append(label_id)
            self.labels.sort()
            DataLabel.add_to_card(card, label_id)
