# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from nagare.i18n import _
from nagare import presentation, ajax, security, component

from .comp import Gallery, Asset, AssetCropper


def render_image(self, h, comp, size, randomize=False, **kw):
    metadata = self.assets_manager.get_metadata(self.filename)
    src = self.assets_manager.get_image_url(self.filename, size)
    if randomize:
        src += '?r=' + h.generate_id()
    return h.img(title=metadata['filename'], alt=metadata['filename'],
                 src=src, **kw)


def render_file(self, h, comp, size, **kw):
    kw['class'] += ' file_icon'
    metadata = self.assets_manager.get_metadata(self.filename)
    res = [h.img(title=metadata['filename'], alt=metadata['filename'],
                 src="img/file-icon.jpg", **kw)]
    if size == 'medium':
        res.append(h.span(metadata['filename']))
    return res


CONTENT_TYPES = {'image/png': render_image,
                 'image/jpeg': render_image,
                 'image/pjpeg': render_image,
                 'image/gif': render_image}


@presentation.render_for(Gallery)
def render(self, h, comp, *args):
    self.load_assets()
    with h.div(id='gal' + self.comp_id):
        with h.div(class_='nbItems'):
            h << comp.render(h, model='badge')
        with h.div(id="card-gallery"):
            h << comp.render(h, self.model)
    return h.root


@presentation.render_for(Gallery, 'view')
def render_Gallery_view(self, h, comp, model):
    model = 'edit' if security.has_permissions('edit', self) else 'anonymous'
    for asset in self.assets:
        h << asset.render(h, model)
    return h.root


@presentation.render_for(Gallery, 'crop')
def render_Gallery_crop(self, h, comp, model):
    return self.cropper.on_answer(self.action)


@presentation.render_for(Gallery, 'cover')
def render_cover(self, h, comp, model):
    cover = self.get_cover()
    if cover:
        h << h.p(component.Component(cover, model='cover'), class_='cover')
    return h.root


@presentation.render_for(Gallery, model='badge')
def render_gallery_badge(self, h, *args):
    """Gallery badge for the card"""
    num_assets = self.num_assets
    if num_assets:
        with h.span(class_='badge'):
            h << h.span(h.i(class_='icon-file-empty'), ' ', num_assets, class_='label')
    return h.root


@presentation.render_for(Gallery, "action")
def render_download(self, h, comp, *args):
    if security.has_permissions('edit', self):
        submit_id = h.generate_id("attach_submit")
        input_id = h.generate_id("attach_input")
        h << h.label((h.i(class_='icon-file-empty'),
                      _("Add file")), class_='btn', for_=input_id)
        with h.form:
            h << h.script(
                u'''
    function valueChanged(e) {
        if (YAHOO.kansha.app.checkFileSize(this, %(max_size)s)) {
            YAHOO.util.Dom.get(%(submit_id)s).click();
            YAHOO.kansha.app.showWaiter();
        } else {
            alert(%(error)s);
        }
    }

    YAHOO.util.Event.onDOMReady(function() {
        YAHOO.util.Event.on(%(input_id)s, 'change', valueChanged);
    });''' %
                {
                    'max_size': ajax.py2js(self.assets_manager.max_size),
                    'input_id': ajax.py2js(input_id),
                    'submit_id': ajax.py2js(submit_id),
                    'error': ajax.py2js(
                        _(u'Max file size exceeded')
                    ).decode('UTF-8')
                }
            )
            submit_action = ajax.Update(
                render=lambda r: r.div(comp.render(r, model=None), r.script('YAHOO.kansha.app.hideWaiter()')),
                component_to_update='gal' + self.comp_id,
            )

            h << h.input(id=input_id, class_='hidden', type="file", name="file", multiple="multiple", maxlength="100",).action(self.add_assets)
            h << h.input(class_='hidden', id=submit_id, type="submit").action(submit_action)
    return h.root


@presentation.render_for(Asset)
@presentation.render_for(Asset, model='thumb')
@presentation.render_for(Asset, model='medium')
@presentation.render_for(Asset, model='cover')
def render_asset(self, h, comp, model, *args):
    res = []
    metadata = self.assets_manager.get_metadata(self.filename)
    kw = {'randomize': True} if model == 'cover' else {}
    kw['class'] = model
    if self.is_cover:
        res.append(h.span(class_='is_cover'))

    meth = CONTENT_TYPES.get(metadata['content-type'], render_file)
    res.append(meth(self, h, comp, model, **kw))
    return res

@presentation.render_for(Asset, model='edit')
def render_Asset_thumb(self, h, comp, model, *args):
    with h.div(class_='asset'):
        action = h.a.action(lambda: comp.answer(('delete', self))).get('onclick')
        onclick = _(u'Are you sure you want to delete this file?')
        onclick = u'if (confirm("%s")) { %s }' % (onclick, action)
        with h.a(class_='delete', title=_(u'Delete'), href='#', onclick=onclick):
            h << h.i(class_='icon-cross')
        if self.is_image():
            with h.a(class_='cover', title=_(u'Configure cover')).action(lambda: comp.answer(('configure_cover', self))):
                if self.is_cover:
                    h << {'style': 'visibility: visible'}
                h << h.i(class_='icon-checkmark')
        with h.a(href=self.assets_manager.get_image_url(self.filename), target='_blank'):
            h << comp.render(h, 'thumb')
    return h.root

@presentation.render_for(Asset, model="anonymous")
def render_asset_anonymous(self, h, comp, model, *args):
    with h.div(class_='asset'):
        with h.a(href=self.assets_manager.get_image_url(self.filename), target='_blank'):
            h << comp.render(h, model="thumb")
    return h.root


@presentation.render_for(AssetCropper)
def render_gallery_cropper(self, h, comp, *args):
    h << h.p(_('Use the controls below to create the cover of your card.'))

    form_id = h.generate_id()
    img_id = h.generate_id()

    with h.form:
        for crop_name in 'crop_left', 'crop_top', 'crop_width', 'crop_height':
            h << h.input(type='hidden', id=form_id + '_' + crop_name).action(getattr(self, crop_name))
        h << h.p(render_image(self.asset, h, comp, 'medium', id=img_id))
        h << h.script(
            "YAHOO.util.Event.onContentReady(%s,"
            "function(){setTimeout(function(){YAHOO.kansha.app.initCrop(%s, %s, %s, %s)}, 500)})" % (
                ajax.py2js(img_id),
                ajax.py2js(img_id),
                ajax.py2js(form_id),
                ajax.py2js(self.crop_width()),
                ajax.py2js(self.crop_height())
            )
        )
        with h.div(class_='buttons'):
            h << h.button(_('Create cover'), class_='btn btn-primary').action(self.commit, comp)
            if self.asset.is_cover:
                h << ' '
                h << h.button(_('Remove cover'), class_='btn delete').action(self.remove_cover, comp)
            h << ' '
            h << h.button(_('Cancel'), class_='btn').action(self.cancel, comp)
    return h.root
