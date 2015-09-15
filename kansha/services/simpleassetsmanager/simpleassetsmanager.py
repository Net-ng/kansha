# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from ..assetsmanager import AssetsManager
from nagare import log
from PIL import Image
from PIL import ImageOps
import json
import os
import uuid


class SimpleAssetsManager(AssetsManager):

    thumb_size = (68, 68)
    medium_width = 425
    cover_size = (medium_width, 250)

    def __init__(self, basedirectory, app_name, **config):
        self.basedirectory = basedirectory
        self.app_name = app_name
        self.max_size = config['max_size']
        super(SimpleAssetsManager, self).__init__()

    def _get_filename(self, file_id, size=None):
        filename = os.path.join(self.basedirectory, file_id)
        if size and size != 'large':
            filename += '.' + size
        return filename

    def _get_metadata_filename(self, file_id):
        return os.path.join(self.basedirectory, '%s.metadata' % file_id)

    def save(self, data, file_id=None, metadata={}, thumb_size=()):
        if file_id is None:
            file_id = unicode(uuid.uuid4())
        with open(self._get_filename(file_id), "w") as f:
            f.write(data)
        # Store metadata
        with open(self._get_metadata_filename(file_id), "w") as f:
            f.write(json.dumps(metadata))

        img = None
        try:
            img = Image.open(self._get_filename(file_id))
        except IOError:
            log.info('Not an image file, skipping medium & thumbnail generation')
        else:
            # Store thumbnail & medium
            kw = {}
            if 'transparency' in img.info:
                kw['transparency'] = img.info["transparency"]

            orig_width, orig_height = img.size

            medium_size = self.medium_width, int(float(self.medium_width) * orig_height / orig_width)
            medium = img.copy()

            medium.thumbnail(medium_size, Image.ANTIALIAS)
            medium.save(self._get_filename(file_id, 'medium'), img.format, quality=75, **kw)  # 'JPEG')

            thumb = ImageOps.fit(img, thumb_size if thumb_size else self.thumb_size, Image.ANTIALIAS)
            thumb.save(self._get_filename(file_id, 'thumb'), img.format, quality=75, **kw)  # 'JPEG')

        return file_id

    def delete(self, file_id):
        files = [self._get_filename(file_id),
                 self._get_filename(file_id, 'thumb'),
                 self._get_filename(file_id, 'medium'),
                 self._get_filename(file_id, 'cover'),
                 self._get_filename(file_id, 'large'),
                 self._get_metadata_filename(file_id)]
        for f in files:
            try:
                os.remove(f)
            except OSError:  # File does not exist
                pass

    def load(self, file_id, size=None):
        filename = self._get_filename(file_id, size)
        with open(filename, "r") as f:
            data = f.read()
        return data, self.get_metadata(file_id)

    def update_metadata(self, file_id, metadata):
        pass

    def get_metadata(self, file_id):
        with open(self._get_metadata_filename(file_id), "r") as f:
            metadata = f.read()
        return json.loads(metadata)

    def get_image_size(self, fileid):
        """Return the image dimensions
        In:
            - ``fileid`` -- file identifier
        Return:
            - a tuple representing the image dimensions (width, height) or (None, None) in case of error
        """
        dim = (None, None)
        try:
            dim = Image.open(self._get_filename(fileid)).size
        except:
            log.error('Could not get image dimensions of %r', fileid, exc_info=True)
        return dim

    def get_image_url(self, file_id, size=None, include_filename=True):
        """Return an image significant URL
        In:
            - ``file_id`` -- file identifier
            - ``size`` -- size to get (thumb, medium, cover, large)
            - ``include_filename`` -- add the filename to the URL or not

        Return:
            - image significant URL
        """
        if self.app_name:
            url = ['', self.app_name, 'assets', file_id, size or 'large']
        else:
            url = ['', 'assets', file_id, size or 'large']
        if include_filename:
            url.append(self.get_metadata(file_id)['filename'])
        return '/'.join(url)

    def create_cover(self, file_id, left, top, width, height):
        """Create the cover version for a file

        In :
          - ``file_id`` -- The asset to make as cover
          - ``left`` -- Left coordinate of the crop origin
          - ``top`` -- Top coordinate of the crop origin
          - ``width`` -- Crop width
          - ``height`` -- Crop height
        """

        # The crop dimensions are given for the medium version.
        # Calculate them for the large version

        medium_img = Image.open(self._get_filename(file_id, 'medium'))
        medium_w, medium_h = medium_img.size

        large_img = Image.open(self._get_filename(file_id))
        large_w, large_h = large_img.size
        kw = {}
        if 'transparency' in large_img.info:
            kw['transparency'] = large_img.info["transparency"]

        left, width = int(float(left) * large_w / medium_w), int(float(width) * large_w / medium_w)
        top, height = int(float(top) * large_h / medium_h), int(float(height) * large_h / medium_h)

        n_img = large_img.crop((left, top, left + width, top + height))
        n_img.thumbnail(self.cover_size, Image.ANTIALIAS)
        n_img.save(self._get_filename(file_id, 'cover'), large_img.format, quality=75, **kw)
