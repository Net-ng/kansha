# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import cgi
import sys
import json
import time
import pstats
import urlparse
import cProfile as profile
from collections import OrderedDict

import webob
import configobj
import pkg_resources

from nagare.i18n import _, _L
from nagare.admin import command
from nagare.namespaces import xhtml5
from nagare import component, wsgi, security, config, log, i18n

from kansha import events
from kansha.card import Card
from kansha import exceptions
from kansha.menu import MenuEntry
from kansha.authentication import login
from kansha import services, notifications
from kansha.services.search import SearchEngine
from kansha.user.usermanager import UserManager
from kansha.user.user_profile import get_userform  # !!!!!!!!!!!!!!!
from kansha.board.boardsmanager import BoardsManager
from kansha.security import SecurityManager, Unauthorized


def run():
    return command.run('kansha.commands')


class Kansha(object):
    """The Kansha root component"""

    def __init__(self, app_title, app_banner, favicon, theme,
                 card_extensions, services_service):
        """Initialization
        """
        self.app_title = app_title
        self.app_banner = app_banner
        self.favicon = favicon
        self.theme = theme
        self.card_extensions = card_extensions
        self._services = services_service

        self.title = component.Component(self, 'tab')
        self.user_menu = component.Component(None)
        self.content = component.Component(None)
        self.user_manager = UserManager()
        self.boards_manager = self._services(
            BoardsManager, self.app_title, self.app_banner, self.theme,
            card_extensions)

        self.home_menu = OrderedDict()
        self.selected = 'board'

    def _on_menu_entry(self, id_):
        """Select a configuration menu entry

        In:
            - ``id_`` -- the id of the selected menu entry
        """
        if id_ == 'boards':
            self.boards_manager.load_user_boards()
        self.content.becomes(self.home_menu[id_].content)
        self.selected = id_

    def initialization(self):
        """ Initialize Kansha application

        Initialize user_menu with current user,
        Initialize last board

        Return:
         - app initialized
        """
        user = security.get_user()
        self.home_menu['boards'] = MenuEntry(
            _L(u'Boards'),
            'table2',
            self.boards_manager
        )
        self.home_menu['profile'] = MenuEntry(
            _L(u'Profile'),
            'user',
            self._services(
                get_userform(
                    self.app_title, self.app_banner, self.theme, user.data.source
                ),
                user.data,
            )
        )
        self.user_menu = component.Component(user)
        if user and self.content() is None:
            self.select_last_board()
        return self

    def _select_board(self, board):
        self.content.becomes(board)
        # if user is logged, update is last board
        user = security.get_user()
        if user:
            user.set_last_board(board)

    def select_board(self, id_):
        """Redirect to a board by id

        In:
          - ``id_`` -- the id of the board
        """
        if not id_:
            return
        board = self.boards_manager.get_by_id(id_)
        if board is not None and not board.archived:
            self.content.becomes(board, 'redirect')
            self.selected = 'board'
        else:
            raise exceptions.BoardNotFound()

    def select_board_by_uri(self, uri):
        """Selected a board by URI

        In:
          - ``uri`` -- the uri of the board
        """
        if not uri:
            return
        board = self.boards_manager.get_by_uri(uri)
        if board is not None and not board.archived:
            self._select_board(board)
        else:
            raise exceptions.BoardNotFound()

    def select_last_board(self):
        """Selects the last used board if it's possible

        Otherwise, content becomes user's home
        """
        user = security.get_user()
        data_board = user.get_last_board()
        if data_board and not data_board.archived and data_board.has_member(user.data):
            self.select_board(data_board.id)
        else:
            self._on_menu_entry('boards')

    def handle_event(self, event):
        if event.is_(events.BoardLeft) or event.is_(events.BoardArchived):
            return self._on_menu_entry('boards')
        elif event.is_(events.NewTemplateRequested):
            return self.boards_manager.create_template_from_board(event.emitter, *event.data)


class MainTask(component.Task):
    def __init__(self, app_title, theme, config, card_extensions, services_service):
        self.app_title = app_title
        self.theme = theme
        self._services = services_service
        self.app_banner = config['pub_cfg']['banner']
        self.favicon = config['pub_cfg']['favicon']
        self.app = services_service(
            Kansha,
            self.app_title,
            self.app_banner,
            self.favicon,
            self.theme,
            card_extensions,
        )
        self.config = config

    def go(self, comp):
        user = security.get_user()
        while user is None:
            # not logged ? Call login component
            comp.call(
                self._services(
                    login.Login,
                    self.app_title,
                    self.app_banner,
                    self.favicon,
                    self.theme,
                    self.config
                )
            )
            user = security.get_user()
            user.update_last_login()

        comp.call(self.app.initialization())
        # Logout
        if user is not None:
            security.get_manager().logout()


class WSGIApp(wsgi.WSGIApp):
    """This application uses a HTML5 renderer"""
    renderer_factory = xhtml5.Renderer

    ConfigSpec = {
        'application': {'as_root': 'boolean(default=True)',
                        'title': 'string(default="")',
                        'banner': 'string(default="")',
                        'theme': 'string(default="kansha_flat")',
                        'favicon': 'string(default="img/favicon.ico")',
                        'disclaimer': 'string(default="")',
                        'activity_monitor': "string(default='')"},
        'locale': {
            'major': 'string(default="en")',
            'minor': 'string(default="US")'
        }
    }

    def set_config(self, config_filename, conf, error):
        super(WSGIApp, self).set_config(config_filename, conf, error)
        conf = configobj.ConfigObj(
            conf, configspec=configobj.ConfigObj(self.ConfigSpec), interpolation='Template')
        config.validate(config_filename, conf, error)

        self._services = services.ServicesRepository(
            config_filename, error, conf
        )

        self.card_extensions = services.CardExtensions(
            config_filename, error, conf
        )

        self.as_root = conf['application']['as_root']
        self.app_title = unicode(conf['application']['title'], 'utf-8')
        self.app_name = conf['application']['name']
        self.theme = conf['application']['theme']
        self.application_path = conf['application']['path']

        # search_engine engine configuration
        self.search_engine = SearchEngine(**conf['search'])
        self._services.register('search_engine', self.search_engine)
        Card.update_schema(self.card_extensions)

        # Make assets_manager available to kansha-admin commands
        self.assets_manager = self._services['assets_manager']

        # other
        self.security = SecurityManager(conf['application']['crypto_key'])
        self.debug = conf['application']['debug']
        self.default_locale = i18n.Locale(
            conf['locale']['major'], conf['locale']['minor'])
        pub_cfg = {
            'disclaimer': conf['application']['disclaimer'].decode('utf-8'),
            'banner': conf['application']['banner'].decode('utf-8'),
            'favicon': conf['application']['favicon'].decode('utf-8')
        }
        self.app_config = {
            'authentication': conf['authentication'],
            'pub_cfg': pub_cfg
        }
        self.activity_monitor = conf['application']['activity_monitor']

    def set_publisher(self, publisher):
        if self.as_root:
            publisher.register_application(self.application_path, '', self,
                                           self)

    def create_root(self):
        return super(WSGIApp, self).create_root(
            self.app_title,
            self.theme,
            self.app_config,
            self.card_extensions,
            self._services
        )

    def start_request(self, root, request, response):
        super(WSGIApp, self).start_request(root, request, response)
        if security.get_user():
            self.set_locale(security.get_user().get_locale())

    def __call__(self, environ, start_response):
        query = environ['QUERY_STRING']
        if ('state=' in query) and (('code=' in query) or ('error=' in query)):
            request = webob.Request(environ)
            environ['QUERY_STRING'] += ('&' + request.params['state'])
            environ['REQUEST_METHOD'] = 'POST'
        if self.debug:
            perf = profile.Profile()
            start = time.time()
            ret = perf.runcall(super(WSGIApp, self).__call__, environ, start_response)
            if time.time() - start > 1:
                stats = pstats.Stats(perf)
                stats.sort_stats('cumtime')
                stats.print_stats(60)
            return ret
        else:
            return super(WSGIApp, self).__call__(environ, start_response)

    def on_exception(self, request, response):
        exc_class, e = sys.exc_info()[:2]
        for k, v in request.POST.items():
            if isinstance(v, cgi.FieldStorage):
                request.POST[k] = u'Content not displayed'
        log.exception(e)
        response.headers['Content-Type'] = 'text/html'
        package = pkg_resources.Requirement.parse('kansha')
        error = pkg_resources.resource_string(
            package, 'static/html/error.html')
        error = unicode(error, 'utf8')
        response.charset = 'utf8'
        data = {'text': u'', 'status': 200,
                'go_back': _(u'Go back'),
                'app_title': self.app_title,
                'app_name': self.app_name,
                'theme': self.theme}
        if exc_class == Unauthorized:
            status = 403
            text = _(u"You are not authorized to access this board")
        elif exc_class == exceptions.BoardNotFound:
            status = 404
            text = _(u"This board doesn't exists")
        elif exc_class == exceptions.NotFound:
            status = 404
            text = _(u"Page not found")
        elif exc_class == exceptions.KanshaException:
            status = 500
            text = _(unicode(e.message))
        else:
            raise
        # Raise exception if debug
        if self.debug:
            raise
        data['status'] = status
        data['text'] = text
        response.status = status
        if request.is_xhr:
            response.body = json.dumps({'details': text, 'status': status})
        else:
            response.text = error % data
        return response

    def on_callback_lookuperror(self, request, response, async):
        """A callback was not found

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``async`` -- is an XHR request ?
        """
        log.exception("\n%s" % request)
        if self.debug:
            raise

    def send_notifications(self, hours, url):

        mail_sender = self._services['mail_sender']
        # Group users by board
        boards = {}
        for subscriber_bo in notifications.get_subscribers():
            # FIXME: don't use the data directly
            subscriber = subscriber_bo.data
            boards.setdefault(subscriber.board.id, {'board': subscriber.board,
                                                    'subscribers': []})['subscribers'].append(subscriber)

        for board in boards.itervalues():
            if not board['board'].archived:
                events = services.ActionLog.get_events_for_data(board['board'], hours)
                for subscriber in board['subscribers']:
                    data = notifications.filter_events(events, subscriber)
                    if not data:
                        continue
                    locale = UserManager.get_app_user(subscriber.user.username).get_locale()
                    self.set_locale(locale)
                    subject, content, content_html = notifications.generate_email(self.app_title, board['board'],
                                                                                  subscriber.user, hours, url, data)
                    mail_sender.send(subject, [subscriber.user.email], content, content_html)
        if self.activity_monitor:
            events = services.ActionLog.get_events_for_data(None, hours)
            new_users = UserManager.get_all_users(hours)

            if not (events or new_users):
                return
            h = xhtml5.Renderer()
            with h.html:
                h << h.h1('Boards')
                with h.ul:
                    for event in events:
                        notif = event.to_string()
                        if event.card:
                            # IDs are interpreted as anchors since HTML4. So don't use the ID of
                            # the card as a URL fragment, because the browser
                            # jumps to it.
                            ev_url = urlparse.urljoin(url, event.board.url)
                            id_ = '%s#id_card_%s' % (ev_url, event.card.id)
                            notif = h.a(notif, href=id_, style='text-decoration: none;')
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

            mail_sender.send('Activity report for '+url, [self.activity_monitor], u'', h.root.write_htmlstring())


def create_pipe(app, *args, **kw):
    '''Use with Apache only, fixes the content-length when gzipped'''

    try:
        from paste.gzipper import middleware
        app = middleware(app)
    except ImportError:
        pass
    return app


app = WSGIApp(lambda *args: component.Component(MainTask(*args)))
