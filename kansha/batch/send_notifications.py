#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import sys


APP = 'kansha'



global apps

app = apps[APP]

# call main
if len(sys.argv) < 3 or not sys.argv[1].isdigit():
    print 'Please provide the timespan (in hours, as integer) of the summary and the root URL of the app'
    sys.exit(0)
app.send_notifications(int(sys.argv[1]), sys.argv[2])
