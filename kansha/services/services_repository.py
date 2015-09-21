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

from nagare import log

from . import components_repository


def set_entry_point(entry_point):
    if not ServicesRepository.entry_point:
        ServicesRepository.entry_point = entry_point


class ServicesRepository(components_repository.ComponentsRepository):

    def __init__(self, conf_section, conf_filename=None, conf=None, error=None,
                 instantiate=True, services=None):
        self.conf_section = conf_section
        self.update(services or {})
        self['services'] = self
        super(ServicesRepository, self).__init__(
            conf_filename, conf, error, instantiate
        )

    def _instantiate(self, comp, conf_filename, component_conf, error):
        return self(comp, conf_filename, component_conf, error)

    def __call__(self, f, *args, **kw):
        services = _check_services_injection(f, self)
        services.update(kw)

        try:
            return f(*args, **services)
        except:
            log.get_logger(
                '.{}.ServicesRepository.__call__'.format(__name__)
            ).error('%s %s %s', f, args, services)
            raise


def _check_services_injection(f, services_repository):
    try:
        args = inspect.getargspec(f.__init__ if isinstance(f, type) else f)
    except TypeError:
        # could not inspect the function
        return {}

    services = dict(zip(reversed(args.args),
                        reversed(args.defaults or ())))
    services.update({name + '_service': service
                     for name, service in services_repository.iteritems()})

    try:
        return {name: services[name]
                for name in args.args
                if name.endswith('_service')}
    except KeyError as e:
        raise ValueError('service {} missing'.format(e.message[:-8]))
