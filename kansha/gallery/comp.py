#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from ..authentication.database import validators
from ..flow import comp as flow
from ..toolbox import overlay
from ..user import usermanager
from .models import DataGallery, DataAsset
from .. import notifications
from cgi import FieldStorage
from nagare import component, security, var
from nagare.i18n import _
from webob.exc import HTTPOk


IMAGE_CONTENT_TYPES = ('image/png', 'image/jpeg', 'image/pjpeg', 'image/gif')


class Gallery(flow.FlowSource):

    def __init__(self, card, assets_manager):
        """Init method

        In:
            - ``card`` -- card component
        """
        self.card = card
        self.assets_manager = assets_manager
        self.data = DataGallery(self.card)

        self.assets = []
        self.overlays = []
        for data_asset in self.data.get_assets():
            self._create_asset_c(data_asset)
        #self.crop_overlay = None

    def _create_asset_c(self, data_asset):
        asset = Asset(data_asset, self.assets_manager)
        asset_thumb = component.Component(asset, 'thumb').on_answer(self.action)
        asset_menu = component.Component(asset, 'menu').on_answer(self.action)
        self.assets.append(asset_thumb)
        self.overlays.append(self._create_overlay_c(asset_thumb, asset_menu))
        return asset

    def _create_overlay_c(self, asset_thumb, asset_menu):
        return component.Component(overlay.Overlay(lambda h, asset_thumb=asset_thumb: asset_thumb.render(h),
                                                   lambda h, asset_menu=asset_menu: asset_menu.render(h),
                                                   dynamic=False, cls='card-edit-form-overlay'))

    @property
    def flow_elements(self):
        return self.assets

    def add_asset(self, new_file):
        """Add one new file to card

        In:
            - ``new_file`` -- new file to add

        Return:
            - The newly created Asset
        """
        validators.validate_file(new_file, self.assets_manager.max_size, _(u'File must be less than %d KB'))
        fileid = self.assets_manager.save(new_file.file.read(),
                                          metadata={'filename': new_file.filename, 'content-type': new_file.type})
        data = {'file': new_file.filename, 'card': self.card.title().text}
        notifications.add_history(self.card.column.board.data, self.card.data, security.get_user().data, u'card_add_file', data)
        return self._create_asset_c(self.data.add_asset(fileid))

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

    def get_asset(self, filename):
        """Return Asset component which match with filename

        In:
            - ``filename`` -- file id
        Return:
            - an Asset component
        """
        return Asset(self.data.get_asset(filename), self.assets_manager)

    def action(self, response):
        action, asset = response[0], response[1]
        if action == "download":
            pass
        elif action == "delete":
            self.delete_asset(asset)
        elif action == "make cover":
            self.make_cover(asset, *list(response[2]))
            # for data_asset in self.data.get_assets():
            #    self._create_asset_c(data_asset)
            # return "YAHOO.kansha.app.hideOverlay();"
        elif action == 'remove_cover':
            self.remove_cover(asset)

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
        self.card.make_cover(asset)
        for a in self.assets:
            a().is_cover = False
        asset.is_cover = True

    def remove_cover(self, asset):
        """Don't use the asset as cover anymore

        In :
          - ``asset`` -- The asset
        """
        self.card.remove_cover()
        asset.is_cover = False

    def delete_asset(self, asset):
        """Delete asset

        Delete asset from card (component and overlay), database
        and asset manager.

        In:
            - ``asset`` -- Asset to delete
        """
        i = 0
        for a in self.assets:
            if a() == asset:
                self.assets.remove(a)
                self.overlays.pop(i)
                self.assets_manager.delete(asset.filename)
                self.data.delete(asset.filename)
                break
            i = i + 1

    def delete_assets(self):
        '''Delete all assets'''
        for asset in self.data.get_assets():
            self.assets_manager.delete(asset.filename)
        self.assets = []
        self.overlays = []


class Asset(flow.FlowElement):

    def __init__(self, data_asset, assets_manager):
        self.filename = data_asset.filename
        self.creation_date = data_asset.creation_date
        self.author = component.Component(usermanager.get_app_user(data_asset.author.username, data=data_asset.author))
        self.assets_manager = assets_manager
        self.is_cover = data_asset.cover is not None
        self.cropper = None

    def is_image(self):
        return self.assets_manager.get_metadata(self.filename)['content-type'] in IMAGE_CONTENT_TYPES

    def download_asset(self, size=None):
        e = HTTPOk()
        data, meta_data = self.assets_manager.load(self.filename, size)
        e.body = data
        e.content_type = str(meta_data['content-type'])
        e.title = meta_data['filename']
        #e.headers['Cache-Control'] = 'max-age=0, must-revalidate, no-cache, no-store'
        raise e

    @property
    def data(self):
        return DataAsset.get_by_filename(self.filename)

    def crop(self, comp, card_component, card_component_id, card_component_model):
        self.cropper = component.Component(AssetCropper(self, card_component, card_component_id, card_component_model))
        comp.becomes(self, model='crop')

    def end_crop(self, comp, answ):
        comp.becomes(self, model='menu')
        comp.answer(('make cover', self, answ))


class AssetCropper(object):

    def __init__(self, asset, card_component, card_component_id, card_component_model):
        self.asset = asset
        self.card_component = card_component
        self.card_component_id = card_component_id
        self.card_component_model = card_component_model
        self.crop_left, self.crop_top, self.crop_width, self.crop_height = var.Var(), var.Var(), var.Var(), var.Var()
