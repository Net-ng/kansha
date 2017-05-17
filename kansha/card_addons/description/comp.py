# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.i18n import _

from kansha import validator
from kansha.board import excel_export
from kansha.validator import clean_text
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

    @staticmethod
    def get_schema_def():
        return schema.Text(u'description')

    def update_document(self, document):
        desc = self.text
        document.description = clean_text(desc) if desc else u''

    def update(self, other):
        self.data.update(other.data)

    @property
    def data(self):
        data = DataCardDescription.get_by_card(self.card.data)
        if data is None:
            data = DataCardDescription.new(self.card.data)
        return data

    @property
    def text(self):
        return self.data.description

    @text.setter
    def text(self, text):
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

    def __nonzero__(self):
        """Return False if the description if empty
        """
        return bool(self.text)

    def delete(self):
        self.data.delete()


@excel_export.get_extension_title_for(CardDescription)
def get_extension_title_CardDescription(card_extension):
    return _(u'Description')


@excel_export.write_extension_data_for(CardDescription)
def write_extension_data_CardDescription(self, sheet, row, col, style):
    text = validator.clean_text(self.text) if self.text else ''
    sheet.write(row, col, text, style)
