#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from __future__ import absolute_import, unicode_literals

import configobj
import pkg_resources
from nagare import config


class Loadable(object):
    component_category = 'loadable'
    load_priority = 0
    config_spec = {}
    component_id = None
    project_name = None

    def __init__(self, conf_filename=None, conf=None, error=None):
        super(Loadable, self).__init__()

    @classmethod
    def set_id(cls, id_):
        cls.component_id = id_

    @classmethod
    def get_id(cls):
        return cls.component_id

    @classmethod
    def get_uid(cls):
        return cls.get_id()

    @classmethod
    def set_project(cls, project):
        cls.project = project

    @classmethod
    def get_project(cls):
        return cls.project


class Service(Loadable):
    component_category = 'service'

# -----------------------------------------------------------------------------


class ComponentsRepository(dict):
    conf_section = None
    entry_point = None
    load_priority = 0

    def __init__(self, conf_filename=None, conf=None, error=None, instantiate=False):
        if conf is not None:
            self.load(conf_filename, conf, error, instantiate)

    def discover(self):
        components = []

        for entry in pkg_resources.iter_entry_points(self.entry_point):
            comp = entry.load()
            comp.set_id(entry.name)
            comp.set_project(entry.dist.project_name)

            components.append(comp)

        return sorted(components, key=lambda comp: comp.load_priority, reverse=True)

    def read_config(self, components, conf_filename, conf, error):
        spec = {comp.get_id(): comp.config_spec for comp in components}
        spec = configobj.ConfigObj({self.conf_section: spec})

        components_conf = configobj.ConfigObj(conf_filename, configspec=spec, interpolation='Template')
        components_conf.merge(conf)
        config.validate(conf_filename, components_conf, error)

        return components_conf[self.conf_section]

    def load(self, conf_filename, conf, error, instantiate):
        components = self.discover()

        components_conf = self.read_config(components, conf_filename, conf, error)

        for comp in components:
            component_conf = components_conf.get(comp.get_id(), {})
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
                if instantiate:
                    comp = self._instantiate(comp, conf_filename, component_conf, error)

                self[comp.get_uid()] = comp
            except:
                print "%s <%s> can't be loaded" % (comp.component_category.capitalize(), comp.get_id())
                raise

        return components

    def _instantiate(self, comp, conf_filename, component_conf, error):
        return comp(conf_filename, component_conf, error)

    def items(self):
        return sorted(super(ComponentsRepository, self).items(),
                      key=lambda (_, v): getattr(v, 'load_priority', None))

    def keys(self):
        return [k for k, _ in self.items()]

    def __iter__(self):
        return iter(self.keys())

    def values(self):
        return [v for _, v in self.items()]
