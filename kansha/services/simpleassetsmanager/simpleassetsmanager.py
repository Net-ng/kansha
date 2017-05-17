# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import json
import os
import uuid

from PIL import Image
from PIL import ImageOps

from nagare import log

from ..assetsmanager import AssetsManager


class SimpleAssetsManager(AssetsManager):

    def __init__(self, config_filename,  error, basedir, baseurl, max_size):
        super(SimpleAssetsManager, self).__init__(config_filename, error)
        self.basedir = basedir
        self.baseurl = baseurl
        self.max_size = max_size

    def copy_cover(self, file_id, new_file_id):
        try:
            data, metadata = self.load(file_id, 'cover')
            with open(self._get_filename(new_file_id, 'cover'), "w") as f:
                f.write(data)
        except IOError:
            # Cover not existing
            pass

    def copy(self, file_id):
        data, metadata = self.load(file_id)
        return self.save(data, metadata=metadata)

    def _get_filename(self, file_id, size=None):
        filename = os.path.join(self.basedir, file_id)
        if size and size != 'large':
            filename += '.' + size
        return filename

    def _get_metadata_filename(self, file_id):
        return os.path.join(self.basedir, '%s.metadata' % file_id)

    def save(self, data, file_id=None, metadata={}, THUMB_SIZE=()):
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

            medium_size = self.MEDIUM_WIDTH, int(float(self.MEDIUM_WIDTH) * orig_height / orig_width)
            medium = img.copy()

            medium.thumbnail(medium_size, Image.ANTIALIAS)
            medium.save(self._get_filename(file_id, 'medium'), img.format, quality=75, **kw)  # 'JPEG')

            thumb = ImageOps.fit(img, THUMB_SIZE if THUMB_SIZE else self.THUMB_SIZE, Image.ANTIALIAS)
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
        with open(self._get_metadata_filename(file_id), "w") as f:
            metadata = f.write(json.dumps(metadata))

    def get_metadata(self, file_id):
        try:
            f = open(self._get_metadata_filename(file_id), "r")
            metadata = json.loads(f.read())
            f.close()
        except IOError:
            log.error('unable to load metadata for ' + self._get_metadata_filename(file_id))
            metadata = {}
        return metadata

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
        if self.baseurl:
            url = [self.baseurl, self.get_entry_name(), file_id, size or 'large']
        else:
            url = ['', self.get_entry_name(), file_id, size or 'large']
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
        n_img.thumbnail(self.COVER_SIZE, Image.ANTIALIAS)
        n_img.save(self._get_filename(file_id, 'cover'), large_img.format, quality=75, **kw)
