# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import os.path

import pkg_resources
from alembic import command
from alembic import config
from nagare.admin import util
from nagare.admin.command import Command


class AlembicRevisionCommand(Command):
    desc = 'Create a new alembic revision file.'

    @staticmethod
    def set_options(optparser):
        optparser.add_option(
            '-m',
            '--message',
            dest='message',
            default=None,
            help="Message string to use with 'revision'"
        )

    @staticmethod
    def run(parser, options, args):
        cfg = config.Config()
        cfg.set_main_option(
            'script_location',
            os.path.join(
                pkg_resources.require('kansha')[0].location,
                'kansha/alembic'
            )
        )
        command.revision(cfg, message=options.message)


class AlembicUpgradeCommand(Command):
    desc = 'Upgrade to a later alembic version.'

    @staticmethod
    def set_options(optparser):
        optparser.usage += ' revision [application]'

    @staticmethod
    def run(parser, options, args):
        if len(args) not in (1, 2):
            parser.error('Bad number of parameters')

        # Read the configuration of the application
        try:
            application = args[1]
        except IndexError:
            application = 'kansha'

        cfg = _build_alembic_config()
        _set_sqlalchemy_uri(cfg, application, parser.error)

        command.upgrade(cfg, args[0])


class AlembicDowngradeCommand(Command):
    desc = 'Revert to a previous version.'

    @staticmethod
    def set_options(optparser):
        optparser.usage += ' revision [application]'

    @staticmethod
    def run(parser, options, args):
        if len(args) not in (1, 2):
            parser.error('Bad number of parameters')

        # Read the configuration of the application
        try:
            application = args[1]
        except IndexError:
            application = 'kansha'

        cfg = _build_alembic_config()
        _set_sqlalchemy_uri(cfg, application, parser.error)

        command.downgrade(cfg, args[0])


class AlembicCurrentCommand(Command):
    desc = "Display alembic's current revision."

    @staticmethod
    def set_options(optparser):
        optparser.usage += ' [application]'
        optparser.add_option(
            '-v',
            '--verbose',
            action='store_const',
            const=True,
            default=False,
            dest='verbose',
            help='Use more verbose output'
        )

    @staticmethod
    def run(parser, options, args):
        if len(args) not in (0, 1):
            parser.error('Bad number of parameters')

        # Read the configuration of the application
        try:
            application = args[0]
        except IndexError:
            application = 'kansha'

        cfg = _build_alembic_config()
        _set_sqlalchemy_uri(cfg, application, parser.error)

        command.current(cfg, verbose=options.verbose)


class AlembicStampCommand(Command):
    desc = "'stamp' alembic's revision table with the given revision; don't run any migrations."

    @staticmethod
    def set_options(optparser):
        optparser.usage += ' revision [application]'
        optparser.add_option(
            '-v',
            '--verbose',
            action='store_const',
            const=True,
            default=False,
            dest='verbose',
            help='Use more verbose output'
        )

    @staticmethod
    def run(parser, options, args):
        if len(args) not in (1, 2):
            parser.error('Bad number of parameters')

        # Read the configuration of the application
        try:
            application = args[1]
        except IndexError:
            application = 'kansha'

        cfg = _build_alembic_config()
        _set_sqlalchemy_uri(cfg, application, parser.error)

        command.stamp(cfg, args[0])


def _set_sqlalchemy_uri(cfg, application, error):
    aconf = util.read_application(application, error)[-1]
    cfg.set_main_option('sqlalchemy.url', aconf['database']['uri'])


def _build_alembic_config():
    cfg = config.Config()
    cfg.set_main_option(
        'script_location',
        os.path.join(
            pkg_resources.require('kansha')[0].location,
            'kansha/alembic'
        )
    )
    return cfg
