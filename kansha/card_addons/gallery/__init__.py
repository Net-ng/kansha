#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import security
from peak.rules import when
from nagare.security import common

from . import view
from .comp import Gallery


@when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, Gallery)")
def _(self, user, perm, gallery):
    """Test if description is editable"""
    return security.has_permissions('edit', gallery.card)