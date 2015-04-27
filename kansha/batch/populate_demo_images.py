#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from StringIO import StringIO
from nagare import local, log
from nagare.database import session
from kansha.card import comp as card
from kansha.gallery import comp as gallery
from kansha.services.dummyassetsmanager import dummyassetsmanager
from kansha.user import comp as user
import pkg_resources

APP_NAME = 'kansha'


class FakeFile(object):

    def __init__(self, data, fname, type):
        self.file = StringIO(data)
        self.filename = fname
        self.type = type
        self.done = 1


def main():
    global apps
    app = apps[APP_NAME]  # @UndefinedVariable

    user1 = user.User('user1')
    local.request.user = user1
    card1 = card.Card(user1.data.boards[0].columns[1].cards[2].id, None, app.assets_manager)
    gal = gallery.Gallery(card1, app.assets_manager)

    package = pkg_resources.Requirement.parse('kansha')
    for i, (fname, ftype) in enumerate((('tie.jpg', 'image/jpeg'),
                                        ('baseball_game.jpg', 'image/jpeg'),
                                        ('LICENSE.txt', 'text/plain'),
                                        ('swimming_pool.jpg', 'image/jpeg'),
                                        )):
        fullname = pkg_resources.resource_filename(package, 'kansha/services/dummyassetsmanager/%s' % fname)
        with open(fullname, 'r') as f:
            data = f.read()
        asset = gal.add_asset(FakeFile(data, fname, ftype))
        if i == 0:
            gal.make_cover(asset, 0, 0, 399, 250)

    log.info('Added image to card "%s" belonging to user "%s"' % (card1.get_title(), user1.username))

    session.commit()  # @UndefinedVariable


# call main
main()
