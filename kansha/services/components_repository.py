# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.services import plugins


class CardExtensions(plugins.Plugins):
    ENTRY_POINTS = 'kansha.card.extensions'
    CONFIG_SECTION = 'card_extensions'
    CONFIGURATORS = {}

    def set_configurators(self, configurators):
        """
        Return a copy of self with
        CONFIGURATORS set.
        """

        repository = self.copy()
        repository.CONFIGURATORS = configurators
        return repository

    def instantiate_items(self, card, action_log, services_service):
        """
        Return items as CardExtension instances for given card.
        """
        return [
            (name, services_service(klass, card, action_log, self.CONFIGURATORS.get(name)))
            for name, klass in self.items()
        ]
