#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import sys
import urlparse

from kansha.user import usermanager
from kansha import notifications
from nagare.namespaces import xhtml

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
    if app.activity_monitor:
        events = notifications.get_events(None, hours)
        new_users = usermanager.UserManager.get_all_users(hours)
        # for event in events:
        #     print event.board.title, notifications.render_event(event)
        # for usr in new_users:
        #     print usr.fullname, usr.username, usr.email, usr.registration_date

        if not (events or new_users):
            return
        h = xhtml.Renderer()
        with h.html:
            h << h.h1('Boards')
            with h.ul:
                for event in events:
                    if event.card:
                        # IDs are interpreted as anchors since HTML4. So don't use the ID of
                        # the card as a URL fragment, because the browser
                        # jumps to it.
                        ev_url = urlparse.urljoin(url, event.board.url)
                        notif = h.a(notifications.render_event(event), href='%s#id_card_%s' % (
                            ev_url, event.card.id), style='text-decoration: none;')
                    else:
                        notif = notifications.render_event(event)
                    h << h.li(u'%s : ' % (event.board.title), notif)
            h << h.h1('New users')
            with h.table(border=1):
                with h.tr:
                    h << h.th('Login')
                    h << h.th('Fullname')
                    h << h.th('Email')
                    h << h.th('Registration date')
                for usr in new_users:
                    with h.tr:
                        h << h.td(usr.username)
                        h << h.td(usr.fullname)
                        h << h.td(usr.email)
                        h << h.td(usr.registration_date.isoformat())

        app.mail_sender.send('Activity report for '+url, [app.activity_monitor], u'', h.root.write_htmlstring())



# call main
if len(sys.argv) < 3 or not sys.argv[1].isdigit():
    print 'Please provide the timespan (in hours, as integer) of the summary and the root URL of the app'
    sys.exit(0)
main(int(sys.argv[1]), sys.argv[2])
