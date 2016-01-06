#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import component, editor, validator

from kansha.cardextension import CardExtension


class CardWeightEditor(editor.Editor, CardExtension):

    """ Card weight Form
    """

    LOAD_PRIORITY = 80

    fields = {'weight'}
    # WEIGHTING TYPES
    WEIGHTING_OFF = 0
    WEIGHTING_FREE = 1
    WEIGHTING_LIST = 2

    def __init__(self, target, action_log, *args):
        """
        In:
         - ``target`` -- Card instance
        """
        editor.Editor.__init__(self, target, self.fields)
        CardExtension.__init__(self, target, action_log)
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
        success = False
        if self.is_validated(self.fields):
            super(CardWeightEditor, self).commit(self.fields)
            success = True
        return success