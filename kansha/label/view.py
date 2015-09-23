# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --
from nagare import component, presentation, ajax, var, security
from nagare.i18n import _
from ..toolbox import overlay
from .comp import Label, CardLabels


def html_hex_to_rgb_tuple(hex_str):
    return tuple(ord(c) for c in hex_str.replace('#', '').decode('hex'))


def color_style(color):
    r, g, b = html_hex_to_rgb_tuple(color)
    style = ['background-color:%s' % color, 'text-shadow:none']
    # Recipe found here : http://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
    # Use a black text for bright background, and white text for dark colors
    if 1 - (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.5:
        style.append('color:#000000')
    else:
        style.append('color:#FFFFFF')
    return ';'.join(style)


@presentation.render_for(Label)
def render_label(self, h, comp, *args):
    """Render the label as a simple colored block (text in it)"""
    h << h.span(self.data.title, class_='card-label', style=color_style(self.data.color))
    return h.root


@presentation.render_for(Label, model='color')
def render_label_color(self, h, comp, *args):
    """Render the label as a simple colored block (no text in it but with a
    tooltip)
    """
    return h.span(class_='card-label', style=color_style(self.data.color), data_tooltip=self.data.title)


@presentation.render_for(Label, model='edit-color')
def render_label_edit_color(self, h, comp, *args):
    """Edit the label color"""
    # If label changed reload columns
    if self._changed():
        h << h.script('reload_columns()')
        self._changed(False)
    h << component.Component(overlay.Overlay(lambda r: comp.render(r, model='color'),
                                             lambda r: comp.render(r,
                                                                   model='edit-color-overlay'),
                                             dynamic=False,
                                             title=_('Change color')))

    return h.root


@presentation.render_for(Label, model='edit-color-overlay')
def render_label_edit_color_overlay(self, h, comp, *args):
    """Color chooser contained in the overlay body"""
    v = var.Var(self.data.color)
    i = h.generate_id()
    h << h.div(id=i, class_='label-color-picker clearfix')
    with h.form:
        h << h.input(type='hidden', value=v(), id='%s-hex-value' % i).action(v)
        h << h.button(_('Save'), class_='btn btn-primary btn-small').action(
            ajax.Update(action=lambda v=v: self.set_color(v())))
        h << ' '
        h << h.button(_('Cancel'), class_='btn btn-small').action(lambda: None)
    h << h.script("YAHOO.kansha.app.addColorPicker(%s)" % ajax.py2js(i))
    return h.root


@presentation.render_for(CardLabels)
def render_cardlabels_(self, h, comp, *args):
    """Show labels inline (used in card summary view)"""
    if self.colors:
        with h.div(class_='inline-labels minimized'):
            h << (component.Component(Label(d), model='color') for d in self.data_labels)
    return h.root


@presentation.render_for(CardLabels, model='list')
def render_cardlabels_list(self, h, comp, *args):
    """Show labels inline with grey label (for card edit view)"""
    h << h.script('YAHOO.kansha.app.hideOverlay();')
    with h.span(class_='inline-labels detailed'):
        h << (component.Component(Label(d)) for d in self.data_labels)
        if not self.data_labels:
            h << h.span('+', class_='card-label add', data_tooltip=_(u'Select labels'))
    return h.root


@presentation.render_for(CardLabels, model='edit')
def render_cardlabels_edit(self, h, comp, *args):
    """Add or remove labels to card"""
    if security.has_permissions('edit', self.card):
        h << self.overlay
    else:
        h << comp.render(h, model="list")
    return h.root


@presentation.render_for(CardLabels, model='overlay')
def render_cardlabels_overlay(self, h, comp, *args):
    """Label chooser contained in the overlay's body"""
    with h.ul(class_='unstyled inline-labels'):
        for _i, label in enumerate(self.get_available_labels(), 1):
            with h.li:
                cls = ['card-label-choose']
                if label.id in self.labels:
                    cls.append('active')
                # Update the list of labels
                action1 = ajax.Update(
                    action=lambda label_id=label.id: self.activate(label_id))
                # Refresh the list
                action2 = ajax.Update(render=lambda r: comp.render(r, model='list'),
                                      component_to_update='list' + self.comp_id)
                with h.a(title=label.color, class_=' '.join(cls),).action(ajax.Updates(action1, action2)):
                    with h.span(class_="card-label", style=color_style(label.color)):
                        h << label.title
                        if label.id in self.labels:
                            h << h.i(class_='icon icon-ok')
    return h.root
