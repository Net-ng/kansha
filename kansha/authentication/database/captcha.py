# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import pkg_resources
import random
import os
import string
from cStringIO import StringIO

# PIL
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from nagare import presentation

APP_NAME = 'kansha'
_PACKAGE = pkg_resources.Requirement.parse(APP_NAME)


def get_resource_filename(path):
    return pkg_resources.resource_filename(_PACKAGE, path)  # @UndefinedVariable


def random_text(length=5):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for dummy in range(length))


class Captcha(object):

    """Render a captcha image for the given text"""

    def __init__(self, text='', background_name='captcha-bg.png', font_name='ashcanbb_bold.ttf', font_size=30):
        self.text = random_text()
        self.background_path = get_resource_filename(
            os.path.join('data', 'captcha', background_name))
        self.font_path = get_resource_filename(
            os.path.join('data', 'captcha', font_name))
        self.font_size = font_size

    def _generate_image(self):
        """Generate the captcha image"""
        font = ImageFont.truetype(self.font_path, self.font_size)
        image = Image.open(self.background_path)
        image = image.convert("RGBA")
        for i, l in enumerate(self.text):
            txt = Image.new('RGBA', (80, 50), (0, 0, 0, 0))
            d = ImageDraw.Draw(txt)
            d.text((0, 0), l, font=font, fill=(9, 92, 110, 255))
            txt = txt.rotate(random.randint(-20, 20))
            image.paste(txt, (30 + 30 * i, 5), txt)
        return image

    def get_image_data(self):
        """Get the image data"""
        image = self._generate_image()
        out = StringIO()
        image.save(out, 'PNG')
        return out.getvalue()


@presentation.render_for(Captcha)
def render_captcha(self, h, comp, *args):
    h << h.img.action(self.get_image_data)
    return h.root
