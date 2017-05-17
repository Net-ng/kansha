#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.services import service, services


class Service(service.Service):
    CATEGORY = 'service'


class ServicesRepository(services.Services):
    ENTRY_POINTS = 'kansha.services'
    CONFIG_SECTION = 'services'
