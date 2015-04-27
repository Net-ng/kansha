#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from datetime import datetime, timedelta

from nagare import log
from nagare.database import session
from kansha.user import usermanager

APP_NAME = 'kansha'

UserConfirmationTimeout = timedelta(minutes=1)


def main():

    before_date = datetime.now() - UserConfirmationTimeout
    log.info('Clearing users that did not confirm their'
             ' email since %s...' % before_date)

    unconfirmed_users = list(
        usermanager.UserManager.get_unconfirmed_users(before_date))

    if not unconfirmed_users:
        log.info("No user found")
    else:
        for user in unconfirmed_users:
            for vote in user.votes:
                vote.delete()
            for bm in user.board_members:
                bm.delete()
            user.delete()
            log.info('- %s (%s) removed' % (user.fullname, user.username))

    session.commit()  # @UndefinedVariable


# call main
main()
