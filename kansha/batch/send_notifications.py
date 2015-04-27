#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import sys

from kansha.user import usermanager
from kansha import notifications

APP = 'kansha'


def main(hours, url):
    global apps
    app = apps[APP]

    # Group users by board
    boards = {}
    for subscriber in notifications.get_subscribers():
        boards.setdefault(subscriber.board.id, {'board': subscriber.board,
                                                'subscribers': []})['subscribers'].append(subscriber)

    for board in boards.itervalues():
        if not board['board'].archived:
            events = notifications.get_events(board['board'], hours)
            for subscriber in board['subscribers']:
                data = notifications.filter_events(events, subscriber)
                if not data:
                    continue
                locale = usermanager.get_app_user(subscriber.member.username).get_locale()
                app.set_locale(locale)
                subject, content, content_html = notifications.generate_email(app.app_title, board['board'],
                                                                              subscriber.member, hours, url, data)
                app.mail_sender.send(subject, [subscriber.member.email], content, content_html)


# call main
if len(sys.argv) < 3 or not sys.argv[1].isdigit():
    print 'Please provide the timespan (in hours, as integer) of the summary and the root URL of the app'
    sys.exit(0)
main(int(sys.argv[1]), sys.argv[2])
