#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation
from nagare.i18n import _
from .comp import FlowElement
import calendar
from datetime import datetime


@presentation.render_for(FlowElement, model='creation_date')
def render(self, h, comp, model, *args):

    span_id = h.generate_id()
    h << h.span(id=span_id, class_="date")

    utcseconds = calendar.timegm(datetime.utctimetuple(self.creation_date))

    h << h.script(
        "YAHOO.kansha.app.utcToLocal('%s', %s, '%s', '%s');" % (span_id, utcseconds, _(u'at'), _(u'on'))
    )

    return h.root
