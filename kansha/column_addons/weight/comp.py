#--
# Copyright (c) 2012-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from kansha.columnextension import ColumnExtension


class Weight(ColumnExtension):
    def __init__(self, column, action_log, configurator):
        super(Weight, self).__init__(column, action_log, configurator)