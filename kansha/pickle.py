#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from __future__ import absolute_import

import pickle

from nagare import database

# if objgraph is installed, it renders a graph that can help finding why
# the object is pickled
try:
    import objgraph
except ImportError:
    objgraph = None


class UnpicklableMixin(object):

    def __reduce__(self):
        if objgraph:
            database.session.expire_all()
            objgraph.show_backrefs([self], max_depth=5)

        raise pickle.PicklingError(
            'This object is not picklable: {!r}'.format(self)
        )
