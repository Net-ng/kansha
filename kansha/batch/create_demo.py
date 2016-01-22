#--
# Copyright (c) 2008-2013 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

#--
# Copyright (c) 2012-2015 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--


"""
Create and (re)build the search index for cards.
It is safe to run it anytime.
Registered as a nagare-admin command.
Usage :
nagare-admin create-index <app name | config file>
"""
from io import BytesIO

from retricon import retricon
import pkg_resources

from nagare import database
from nagare.admin import util, command

from kansha.user.usermanager import UserManager


# FIXME: too low level
def create_demo(app):
    # demo users
    user_manager = UserManager()
    assets_manager = app.assets_manager
    for i in xrange(1, 4):
        email = u'user%d@net-ng.com' % i
        username = u'user%d' % i
        identicon = retricon(email.encode(), tiles=7, width=140)
        icon_file = BytesIO()
        identicon.save(icon_file, 'PNG')
        assets_manager.save(
            icon_file.getvalue(),
            username,
            {'filename': '%s.png' % username})
        picture = assets_manager.get_image_url(username, 'thumb')
        user = user_manager.create_user(username, u'password', u'user %d' % i, email, picture=picture)
        user.confirm_email()
    database.session.flush()
    # demo templates
    # TODO


class CreateDemo(command.Command):

    desc = 'Create demo users and contents.'

    @staticmethod
    def set_options(optparser):
        optparser.usage += ' [application]'

    @staticmethod
    def run(parser, options, args):

        try:
            application = args[0]
        except IndexError:
            application = 'kansha'

        (cfgfile, app, dist, conf) = util.read_application(application,
                                                           parser.error)
        requirement = (
            None if not dist
            else pkg_resources.Requirement.parse(dist.project_name)
        )
        data_path = (
            None if not requirement
            else pkg_resources.resource_filename(requirement, '/data')
        )

        (active_app, databases) = util.activate_WSGIApp(
            app, cfgfile, conf, parser.error, data_path=data_path)
        for (database_settings, populate) in databases:
            database.set_metadata(*database_settings)
        if active_app:
            create_demo(active_app)
