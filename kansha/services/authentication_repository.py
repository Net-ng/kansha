from __future__ import absolute_import, unicode_literals

from nagare.services import plugin, plugins
from .services_repository import Service


class Authentication(plugin.Plugin):
    CATEGORY = 'authentication'


class AuthenticationsRepository(Service, plugins.Plugins):
    ENTRY_POINTS = 'kansha.authentication'
    CONFIG_SECTION = 'authentication'

    def __init__(self, conf_filename=None, error=None, services_service=None):
        plugins.Plugins.__init__(self, conf_filename, error, self.config)

    def register(self, name, plugin):
        if plugin.config['activated']:
            self[name] = plugin

    # try:
    #     component_conf.update({'root': conf['root']})
    # except KeyError:
    #     pass
    # try:
    #     component_conf.update({'here': conf['here']})
    # except KeyError:
    #     pass
