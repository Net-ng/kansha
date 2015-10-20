#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from __future__ import absolute_import, unicode_literals

import inspect

from . import components_repository


class ServiceMissing(Exception):
    pass


class Service(components_repository.Loadable):
    component_category = 'service'


class ServicesRepository(components_repository.ComponentsRepository):
    entry_point = 'kansha.services'
    conf_section = 'services'

    def __init__(self, conf_filename=None, conf=None, error=None):
        self.metadata = set()
        super(ServicesRepository, self).__init__(conf_filename, conf, error)

    def create(self, cls, conf_filename, component_conf, error):
        return cls(conf_filename, component_conf, error)

    def check_services_injection(self, f):
        args = inspect.getargspec(f.__init__ if isinstance(f, type) else f)

        services = dict(zip(reversed(args.args), reversed(args.defaults or ())))
        services.update({name + '_service': service for name, service in self.items()})
        services['services_service'] = self

        try:
            return {name: services[name] for name in args.args if name.endswith('_service')}
        except KeyError as e:
            raise ServiceMissing(e.args[0][:-8])

    def __call__(self, f, *args, **kw):
        services = self.check_services_injection(f)
        services.update(kw)

        return f(*args, **services)
