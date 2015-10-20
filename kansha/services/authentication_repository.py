from __future__ import absolute_import, unicode_literals

from .components_repository import Loadable, ComponentsRepository
from .services_repository import Service


class Authentication(Loadable):
    component_category = 'authentication'


class AuthenticationsRepository(Service, ComponentsRepository):
    entry_point = 'kansha.authentication'
    conf_section = 'authentication'

    def __init__(self, conf_filename=None, conf=None, error=None, services_service=None):
        self.services = services_service
        ComponentsRepository.__init__(self, conf_filename, conf, error)

    def __call__(self, comp, conf_filename, component_conf, error):
        """Inject config as variable class"""
        comp.config = component_conf
        return comp

    def load(self, conf_filename, conf, error):
        components = self.discover()

        components_conf = self.read_config(components, conf_filename, conf, error)

        for comp in components:
            component_conf = components_conf.get(comp.get_id(), {})
            # Test if auhtentication module is activated
            if not component_conf['activated']:
                continue
            try:
                component_conf.update({'root': conf['root']})
            except KeyError:
                pass
            try:
                component_conf.update({'here': conf['here']})
            except KeyError:
                pass

            if comp.get_uid() in self:
                print 'Name conflict: %s <%s> already defined' % (comp.component_category, comp.get_uid())
                raise NameError(comp.get_id())

            try:
                self[comp.get_uid()] = self(comp, conf_filename, component_conf, error)
            except:
                print "%s <%s> can't be loaded" % (comp.component_category.capitalize(), comp.get_id())
                raise

        return components
