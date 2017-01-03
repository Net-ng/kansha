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
Create the demo users.
Registered as a nagare-admin command.
Usage :
nagare-admin create-demo <app name | config file>
"""
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
        user = user_manager.create_user(username, u'password', u'user %d' % i, email)
        user.confirm_email()
        appuser = user_manager.get_app_user(username, user)
        appuser.reset_avatar(assets_manager)
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
