# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from .. import validator


class Title(object):
    """Title component.

    ``class variables``:
      - field_type  -- type of input
    """
    # Render mode in edit mode
    field_type = 'textarea'

    def __init__(self, parent):
        """Initialization

        In:
          - ``parent`` -- parent of title
        """
        self.parent = parent
        self.text = parent.get_title() or u''

    def change_text(self, text):
        """Change the title of our wrapped object

        In:
            - ``text`` -- the new title
        Return:
            - the new title

        """
        if text is None:
            return
        text = text.strip()
        if text:
            text = validator.clean_text(text)
            self.text = text
            self.parent.set_title(text)
            return text
