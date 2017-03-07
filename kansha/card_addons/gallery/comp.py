#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import random

from peak.rules import when
from cgi import FieldStorage
from webob.exc import HTTPOk

from nagare.i18n import _
from nagare.security import common
from nagare import component, security, var

from kansha import validator
from kansha.user import usermanager
from kansha.cardextension import CardExtension
from kansha.services.actionlog.messages import render_event
from kansha.services.assetsmanager import AssetsManager

from .models import DataAsset


IMAGE_CONTENT_TYPES = ('image/png', 'image/jpeg', 'image/pjpeg', 'image/gif')


@when(render_event, "action=='card_add_file'")
def render_event_card_add_file(action, data):
    return _(u'User %(author)s has added file "%(file)s" to card "%(card)s"') % data


class Gallery(CardExtension):

    LOAD_PRIORITY = 40

    def __init__(self, card, action_log, configurator, assets_manager_service):
        """Init method

        In:
            - ``card`` -- card component
        """
        super(Gallery, self).__init__(card, action_log, configurator)
        self.assets_manager = assets_manager_service
        self.assets = []
        self.comp_id = str(random.randint(10000, 100000))
        self.model = 'view'
        self.cropper = component.Component()

    @property
    def num_assets(self):
        return DataAsset.count_for(self.card.data)

    def load_assets(self):
        if not self.assets:
            for asset_data in DataAsset.get_all(self.card.data):
                self.create_asset(asset_data)

    def delete_asset(self, asset):
        """Delete asset

        Delete asset from card (component and overlay), database
        and asset manager.

        In:
            - ``asset`` -- Asset to delete
        """
        for a in self.assets:
            if a() is asset:
                self.assets.remove(a)
                break
        DataAsset.remove(self.card.data, asset.filename)
        # asset.delete()
        self.assets_manager.delete(asset.filename)

    def delete(self):
        self.load_assets()
        for asset in self.assets:
            self.assets_manager.delete(asset().filename)
        DataAsset.remove_all(self.card.data)
        self.assets = []

    def update(self, other):
        other.load_assets()
        for asset_comp in other.assets:
            asset = asset_comp()
            new_asset = self._add_asset(asset.file_info)
            if asset.is_cover:
                cropper = asset.cropper_info
                self.make_cover(new_asset, **cropper)

    def action(self, response):
        action, asset = response[0], response[1]
        if action == 'delete':
            self.delete_asset(asset)
        elif action == 'configure_cover':
            self.configure_cover(asset)
        elif action == 'make_cover':
            left, top, width, height = response[2:]
            self.make_cover(asset, left, top, width, height)
        elif action == 'cancel_cover':
            self.model = 'view'
        elif action == 'remove_cover':
            self.remove_cover(asset)

    def create_asset(self, data_asset):
        asset = Asset(data_asset, self.assets_manager)
        asset_comp = component.Component(asset).on_answer(self.action)
        self.assets.append(asset_comp)
        return asset

    def add_asset(self, new_file):
        """Add one new file to card

        In:
            - ``new_file`` -- new file to add

        Return:
            - The newly created Asset
        """
        file_info = validator.validate_file(new_file, self.assets_manager.max_size, _(u'File must be less than %d KB'))
        return self._add_asset(file_info)

    def _add_asset(self, file_info):
        user = security.get_user()
        fileid = self.assets_manager.save(file_info['data'],
                                          metadata={'filename': file_info['filename'], 'content-type': file_info['content_type']})
        data = {'file': file_info['filename'], 'card': self.card.get_title()}
        self.action_log.add_history(user, u'card_add_file', data)
        return self.create_asset(DataAsset.add(fileid, self.card.data, user.data))

    def add_assets(self, new_files):
        """Add new assets to the card

        In:
            - ``new_files`` -- new files to add
        """
        if isinstance(new_files, FieldStorage):
            self.add_asset(new_files)
        else:
            for new_file in new_files:
                self.add_asset(new_file)

    def configure_cover(self, asset):
        self.model = 'crop'
        self.cropper.call(AssetCropper(asset))

    def make_cover(self, asset, left, top, width, height):
        """Make the given asset as cover for the card

        In :
          - ``asset`` -- The asset to make as cover
          - ``left`` -- Left coordinate of the crop origin
          - ``top`` -- Top coordinate of the crop origin
          - ``width`` -- Crop width
          - ``height`` -- Crop height
        """
        self.assets_manager.create_cover(asset.filename, left, top, width, height)
        DataAsset.set_cover(self.card.data, asset.data)
        for a in self.assets:
            a().is_cover = False
        asset.is_cover = True
        asset.update_metadata(
            {
                'cropper': {
                    'left': left,
                    'top': top,
                    'width': width,
                    'height': height
                }
            }
        )
        self.model = 'view'

    def get_cover(self):
        cover_data = DataAsset.get_cover(self.card.data)
        if not cover_data:
            return None

        return Asset(cover_data, self.assets_manager)

    def remove_cover(self, asset):
        """Don't use the asset as cover anymore

        In :
          - ``asset`` -- The asset
        """
        DataAsset.remove_cover(self.card.data)
        asset.is_cover = False
        self.model = 'view'


class Asset(object):

    def __init__(self, data_asset, assets_manager_service):
        self.filename = data_asset.filename
        self.creation_date = data_asset.creation_date
        self.author = component.Component(usermanager.UserManager.get_app_user(data_asset.author.username, data=data_asset.author))
        self.assets_manager = assets_manager_service
        self.is_cover = data_asset.cover is not None
        self.metadata = self.assets_manager.get_metadata(self.filename)

    @property
    def content_type(self):
        return self.metadata['content-type']

    @property
    def cropper_info(self):
        width, height = AssetsManager.COVER_SIZE
        defaults = {'left': 0, 'top': 0, 'width': width, 'height': height}
        return self.metadata.get('cropper', defaults)

    def update_metadata(self, metadata):
        self.metadata.update(metadata)
        self.assets_manager.update_metadata(self.filename, self.metadata)

    @property
    def file_info(self):
        data, meta_data = self.assets_manager.load(self.filename, None)
        return {
            'data': data,
            'content_type': meta_data['content-type'],
            'filename': meta_data['filename']
        }

    def is_image(self):
        return self.content_type in IMAGE_CONTENT_TYPES

    @property
    def data(self):
        return DataAsset.get_by_filename(self.filename)

    def cancel(self, comp, answer):
        comp.answer()


class AssetCropper(object):

    def __init__(self, asset):
        self.asset = asset
        self.crop_left = var.Var(0)
        self.crop_top = var.Var(0)
        self.crop_width = var.Var(425)
        self.crop_height = var.Var(250)

    def commit(self, comp):
        comp.answer(('make_cover', self.asset, self.crop_left(), self.crop_top(), self.crop_width(), self.crop_height()))

    def remove_cover(self, comp):
        comp.answer(('remove_cover', self.asset))

    def cancel(self, comp):
        comp.answer(('cancel_cover', self.asset))


@when(common.Rules.has_permission, "user and (perm == 'edit') and isinstance(subject, Gallery)")
def has_permission_Gallery_edit(self, user, perm, gallery):
    """Test if description is editable"""
    return security.has_permissions('edit', gallery.card)