# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import string
import ntpath
import re

from nagare import validator
from nagare.i18n import _, _L


# mail regex extracted from http://www.regular-expressions.info/email.html
MAIL_RE = r"(?i)^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"


def validate_identifier(value, start_with_uppercase_letter=False, max_len=256):
    """Validate an identifier: only letters, digits or underscore characters are accepted"""
    if not value:
        raise ValueError(_("Should not be empty"))

    safe_chars = set("_%s%s" % (string.ascii_letters, string.digits))
    ok = all(c in safe_chars for c in value)
    if not ok:
        raise ValueError(_('Should only contain ascii letters, digits or underscore characters'))

    if start_with_uppercase_letter:
        if value[0] not in string.ascii_uppercase:
            raise ValueError(_("Should start with an uppercase ascii letter"))
    else:
        if value[0] not in string.ascii_letters:
            raise ValueError(_("Should start with an ascii letter"))

    if len(value) > max_len:
        raise ValueError(
            _("Identifier too long (max. %d characters)") % max_len)

    return value


def validate_file(data, max_size=None, msg=_('Size must be less than %d KB')):
    """Validate a 'file' input data against the max size in KB"""
    # check against the first roundtrip with the client
    if data is None or isinstance(data, basestring):
        return None

    if data.done == -1:
        raise ValueError(_('Transfer was interrupted'))

    # gets the file size (it's a StringIO)
    data.file.seek(0, 2)  # 0 from EOF
    filesize = data.file.tell()
    data.file.seek(0)

    if max_size is not None and filesize > max_size * 1024:
        raise ValueError(msg % max_size)

    filedata = data.file.read()
    data.file.seek(0)

    # some browsers (i.e. Internet Explorer) send the full path of the file
    # instead of the filename
    # so, we remove the path from the filename
    filename = ntpath.basename(unicode(data.filename))

    return {'filename': filename,
            'data': filedata,
            'content_type': unicode(data.type)}


def validate_non_empty_string(value, msg=_L("Required field")):
    """Check that the value is a non-empty string"""
    # strip whitespace characters
    return validator.StringValidator(value, strip=True).not_empty(_(msg)).to_string()


def validate_email(value, required_msg=_L("Required field"), invalid_msg=_L("Invalid email address")):
    """Check that the value is a valid email address"""
    if not value:
        raise ValueError(_(required_msg))

    # convert to lowercase
    value = value.lower()

    if len(value) > 7:
        if re.match(MAIL_RE, value):
            return value

    raise ValueError(_(invalid_msg))


def validate_password(value):
    value = validate_non_empty_string(value)

    # check password complexity
    min_len = 6
    if len(value) < min_len:
        raise ValueError(_("Password too short: should have at least %d characters")
                         % min_len)

    return value
