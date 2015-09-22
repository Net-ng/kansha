# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from lxml import html
from lxml.html.clean import Cleaner
from nagare import i18n
from nagare import validator


def clean_text(text):
    return html.fromstring(text).text_content()

def clean_html(text):
    cleaner = Cleaner(style=False)
    return cleaner.clean_html(text)


class BoolValidator(validator.Validator):
    """Conversion and validation of integers
    """

    def __init__(self, value, strip=True, *args, **kw):
        """Initialisation

        Check that the value is a bool

        In:
          - ``v`` -- value to validate
        """
        try:
            if isinstance(value, basestring):
                value = value.strip()

                if value.lower() in ('yes', 'on', 'true', '1'):
                    self.value = True
                elif value.lower() in ('no', 'off', 'false', '0'):
                    self.value = False
                else:
                    self.value = False
            else:
                self.value = bool(value)
        except (ValueError, TypeError):
            raise ValueError(i18n._(u'Must be a boolean'))

    to_bool = validator.Validator.__call__
