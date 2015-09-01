# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from .comp import Gallery, Asset, AssetCropper
from nagare import presentation, var, ajax, security
from nagare.i18n import _, _N


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
    with h.div(class_='nbItems'):
        h << h.script(u'YAHOO.kansha.app.closeModal();')
        h << comp.render(h, model='badge')
    with h.div(id="card-gallery"):
        if security.has_permissions('edit', self):
            for overlay in self.overlays:
                h << overlay
        else:
            for asset in self.assets:
                h << asset.render(h, model="anonymous")

    return h.root


@presentation.render_for(Gallery, "download")
def render_download(self, h, comp, *args):
    if security.has_permissions('edit', self):
        v_file = var.Var()
        submit_id = h.generate_id("attach_submit")
        input_id = h.generate_id("attach_input")
        h << h.label((h.i(class_='icon-file icon-grey'),
                      _("Add file")), class_='btn btn-small', for_=input_id)
        with h.form:
            h << h.script(u'''
    function valueChanged(e) {
        if (YAHOO.kansha.app.checkFileSize(this, %(max_size)s)) {
            YAHOO.util.Dom.get('%(submit_id)s').click();
            YAHOO.kansha.app.showModal('oip');
        } else {
            alert('%(error)s');
        }
    }

    YAHOO.util.Event.onDOMReady(function() {
        YAHOO.util.Event.on('%(input_id)s', 'change', valueChanged);
    });
''' % {'max_size': self.assets_manager.max_size, 'input_id': input_id, 'submit_id': submit_id, 'error': _(u'Max file size exceeded')})
            h << h.input(id=input_id, style="position:absolute;left:-1000px;", type="file", name="file", multiple="multiple", maxlength="100",).action(v_file)
            h << h.input(style="position:absolute;left:-1000px;", id=submit_id, type="submit").action(lambda: self.add_assets(v_file()))
    return h.root


@presentation.render_for(Gallery, model='badge')
def render_gallery_badge(self, h, *args):
    """Gallery badge for the card"""
    if self.assets:
        label = _N('file', 'files', len(self.assets))
        h << h.span(h.i(class_='icon-file icon-grey'), ' ', len(self.assets), class_='label', data_tooltip=label)
    return h.root


@presentation.render_for(Asset, model="anonymous")
def render_asset_anonymous(self, h, comp, model, *args):
    return h.a(comp.render(h, model="thumb"), target='_blank',
               onclick="window.open('%s');YAHOO.kansha.app.hideOverlay()" % self.assets_manager.get_image_url(self.filename))


@presentation.render_for(Asset)
@presentation.render_for(Asset, model='medium')
@presentation.render_for(Asset, model='thumb')
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


@presentation.render_for(Asset, model='flow')
def render_asset_flow(self, h, comp, *args):
    with h.div(class_='comment'):
        with h.div(class_='left'):
            h << self.author.render(h, model='avatar')
        with h.div(class_='right'):
            h << self.author.render(h, model='fullname')
            h << _(' added a file ')
            h << comp.render(h, 'creation_date')
            with h.div(class_='contents'):
                with h.p:
                    h << h.SyncRenderer().a(comp.render(h, model='medium'),
                                            href=self.assets_manager.get_image_url(self.filename),
                                            target='_blank')
    return h.root


@presentation.render_for(Asset, 'menu')
def render_overlay_menu(self, h, comp, *args):

    id_ = h.generate_id()

    card_cmp, card_id, card_model = h.get_async_root().component, h.get_async_root().id, h.get_async_root().model

    with h.div(id=id_):

        with h.ul:
            h << h.li(h.a(_('Open'), target='_blank',
                          onclick="window.open('%s');YAHOO.kansha.app.hideOverlay()" % self.assets_manager.get_image_url(self.filename)))
            h << h.li(h.a(_('Delete')).action(lambda: comp.answer(('delete', self))))
            if self.is_image():
                if self.is_cover:
                    h << h.li(h.a(_('Remove cover')).action(
                        lambda: comp.answer(('remove_cover', self))))
                else:
                    h << h.li(h.a(_('Make cover')).action(
                        ajax.Update(
                            render=lambda h: comp.render(h),
                            action=lambda: self.crop(comp, card_cmp, card_id, card_model),
                            component_to_update=id_)
                        )
                    )
    return h.root


@presentation.render_for(Asset, model='crop')
def render_gallery_crop(self, h, comp, *args):

    h << self.cropper.on_answer(lambda answ: self.end_crop(comp, answ))

    return h.root


@presentation.render_for(AssetCropper)
def render_gallery_cropper(self, h, comp, *args):
    crop_width, crop_height = 425, 250

    h << h.p(_('Use the controls below to create the cover of your card.'))

    form_id, img_id = h.generate_id(), h.generate_id()

    with h.form:
        for crop_name in 'crop_left', 'crop_top', 'crop_width', 'crop_height':
            h << h.input(type='hidden', id=form_id + '_' + crop_name).action(getattr(self, crop_name))
        h << h.p(render_image(self.asset, h, comp, 'medium', id=img_id))
        h << h.script("""YAHOO.util.Event.onContentReady('%s',
                            function(){YAHOO.kansha.app.initCrop('%s', '%s', %s, %s)});""" % (img_id,
                                                                                             img_id,
                                                                                             form_id,
                                                                                             crop_width,
                                                                                             crop_height),
                      type="text/javascript")
        h << h.input(type='submit',
                     value=_('Done'),
                     class_='btn btn-primary btn-small').action(ajax.Update(render=lambda r: self.card_component.render(r, self.card_component_model),
                                                                            action=lambda: comp.answer((int(self.crop_left() or 0),
                                                                                                        int(self.crop_top() or 0),
                                                                                                        int(self.crop_width() or crop_width),
                                                                                                        int(self.crop_height() or crop_height))),
                                                                            component_to_update=self.card_component_id)
                                                                )
    return h.root
