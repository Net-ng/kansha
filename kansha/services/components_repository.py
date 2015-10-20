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


# -----------------------------------------------------------------------------


class ComponentsRepository(dict):
    conf_section = None
    entry_point = None
    load_priority = 0

    def __init__(self, conf_filename=None, conf=None, error=None):
        if conf is not None:
            self.load(conf_filename, conf, error)

    @classmethod
    def discover(cls):
        components = []

        for entry in pkg_resources.iter_entry_points(cls.entry_point):
            comp = entry.load()
            comp.set_id(entry.name)
            comp.set_project(entry.dist.project_name)

            components.append(comp)

        return sorted(components, key=lambda comp: comp.load_priority)

    def read_config(self, components, conf_filename, conf, error):
        spec = {comp.get_id(): comp.config_spec for comp in components}
        spec = configobj.ConfigObj({self.conf_section: spec})

        components_conf = configobj.ConfigObj(conf_filename, configspec=spec, interpolation='Template')
        components_conf.merge(conf)
        config.validate(conf_filename, components_conf, error)

        return components_conf[self.conf_section]

    def create(self, factory, conf_filename, component_conf, error):
        return factory

    def load(self, conf_filename, conf, error):
        components = self.discover()

        components_conf = self.read_config(components, conf_filename, conf, error)

        for comp in components:
            component_conf = components_conf.get(comp.get_id(), {})
            component_conf.update({'root': conf['root'], 'here': conf['here']})

            if comp.get_uid() in self:
                print 'Name conflict: %s <%s> already defined' % (comp.component_category, comp.get_uid())
                raise NameError(comp.get_id())

            try:
                component = self.create(comp, conf_filename, component_conf, error)
                if component is not None:
                    self[comp.get_uid()] = component
            except:
                print "%s <%s> can't be loaded" % (comp.component_category.capitalize(), comp.get_id())
                raise

        return components

    def items(self):
        return sorted(super(ComponentsRepository, self).items(), key=lambda (_, v): v.load_priority)

    def keys(self):
        return [k for k, _ in self.items()]

    def __iter__(self):
        return iter(self.keys())

    def values(self):
        return [v for _, v in self.items()]
