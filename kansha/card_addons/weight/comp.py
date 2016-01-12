#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from peak.rules import when
from nagare import component, editor, validator

from kansha.cardextension import CardExtension
from kansha.services.actionlog.messages import render_event

from .models import DataCardWeight


@when(render_event, "action=='card_weight'")
def render_event_card_weight(action, data):
    return _(u'Card "%(card)s" has been weighted from (%(from)s) to (%(to)s)') % data


class CardWeightEditor(CardExtension):

    """ Card weight Form
    """

    LOAD_PRIORITY = 80

    # WEIGHTING TYPES
    WEIGHTING_OFF = 0
    WEIGHTING_FREE = 1
    WEIGHTING_LIST = 2

    def __init__(self, card, action_log, *args):
        """
        In:
         - ``target`` -- Card instance
        """
        CardExtension.__init__(self, card, action_log)
        self.card = card
        self.weight = editor.Property(self.data.weight)
        self.weight.validate(self.validate_weight)
        self.action_button = component.Component(self, 'action_button')

    def copy(self, parent, additional_data):
        self.data.copy(parent.data)
        return super(CardWeightEditor, self).copy(parent, additional_data)

    @property
    def data(self):
        data = DataCardWeight.get_by_card(self.card.data)
        if data is None:
            data = DataCardWeight(card=self.card.data)
        return data

    def validate_weight(self, value):
        """
        Integer or empty
        """
        if value:
            validator.IntValidator(value).to_int()
        return value

    def commit(self):
        success = False
        if self.weight.error is None:
            self.data.weight = self.weight.value
            success = True
        return success