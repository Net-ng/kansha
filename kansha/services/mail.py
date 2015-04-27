# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.Utils import COMMASPACE, formatdate

from nagare import log


class MailSender(object):

    def __init__(self, host, port, default_sender):
        self.host = host
        self.port = port
        self.default_sender = default_sender
        log.debug(
            'The mail sender will connect to %s on port %s' % (host, port))

    def set_application_url(self, application_url):
        self.application_url = application_url

    def _smtp_send(self, from_, to, contents):
        smtp = smtplib.SMTP(self.host, self.port)
        try:
            smtp.sendmail(from_, to, contents)
        except Exception as e:
            log.exception(e)
        finally:
            smtp.close()

    def send(self, subject, to, content, html_content=None, from_='', cc=[], bcc=[],
             type='plain', mpart_type='alternative'):
        """Sends an email

        In:
         - ``subject`` -- email object
         - ``to`` -- To email's list
         - ``content`` --  email content
         - ``from_`` -- email sender
         - ``cc`` --  CC email's list
         - ``bcc`` -- BCC email's list
         - ``type`` --  email type
         - ``mpart_type`` -- email part type

        """
        from_ = from_ if from_ else self.default_sender
        # create the message envelop
        msg = MIMEMultipart(mpart_type)
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg['From'] = from_
        msg['To'] = COMMASPACE.join(to)

        if cc:
            msg['Cc'] = COMMASPACE.join(cc)

        # attach the mail content
        charset = 'us-ascii'
        if isinstance(content, unicode):
            content = content.encode('UTF-8')
            charset = 'UTF-8'
        msg.attach(MIMEText(content, type, charset))
        if html_content:
            msg.attach(MIMEText(html_content, 'html', charset))

        # log
        log.info('Sending mail:\n  subject=%s\n  from=%s\n  to=%s\n  cc=%s\n  bcc=%s',
                 subject, from_, to, cc, bcc)
        log.debug('Mail content:\n' + content)

        # post the email to the SMTP server
        self._smtp_send(from_, to + cc + bcc, msg.as_string())


class NullMailSender(MailSender):

    """Mail sender that does not send any email"""

    def _smtp_send(self, from_, to, contents):
        pass  # do nothing
