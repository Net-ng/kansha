# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
from kansha import validator
from kansha.services.search import schema
from kansha.cardextension import CardExtension

from .models import DataCardDescription


class CardDescription(CardExtension):
    """Description component,

    This component can be used for with all element which have a description
    field.
    Examples are available in card and board modules
    """

    LOAD_PRIORITY = 20

    def __init__(self, card, action_log, configurator):
        """Initialization

        In:
            - ``card`` -- the card
        """
        super(CardDescription, self).__init__(card, action_log, configurator)
        self.text = self.get_description()

    @staticmethod
    def get_schema_def():
        return schema.TEXT()

    def to_document(self):
        return self.text

    def copy(self, parent, additional_data):
        self.data.copy(parent.data)
        return super(CardDescription, self).copy(parent, additional_data)

    @property
    def data(self):
        data = DataCardDescription.get_by_card(self.card.data)
        if data is None:
            data = DataCardDescription(card=self.card.data)
        return data

    def get_description(self):
        return self.data.description

    def set_description(self, text):
        self.data.description = text

    def change_text(self, text):
        """Edit the description

        In:
            - ``text`` -- the text of the description
        """
        # historically, canceling the description edition calls this function with None.
        # FIXME: that should not happen.
        if text is None:
            return
        text = text.strip()
        if text:
            text = validator.clean_html(text)
        self.text = text
        self.set_description(text)

    def __nonzero__(self):
        """Return False if the description if empty
        """
        return bool(self.text)
