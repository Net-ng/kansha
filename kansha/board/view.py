# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import json

from nagare import presentation, security, ajax, component, var
from nagare.i18n import _

from kansha import notifications
from kansha.board.boardconfig import WeightsSequenceEditor
from kansha.toolbox import overlay

from ..toolbox import popin, remote
from .boardconfig import BoardLabels, BoardProfile, BoardConfig, BoardBackground, BoardWeights
from .comp import (BOARD_PRIVATE, BOARD_PUBLIC,
                   COMMENTS_OFF, COMMENTS_PUBLIC, COMMENTS_MEMBERS,
                   VOTES_OFF, VOTES_PUBLIC, VOTES_MEMBERS,
                   WEIGHTING_FREE, WEIGHTING_LIST, WEIGHTING_OFF)
from .comp import (Board, Icon, NewBoard, BoardTitle,
                   BoardDescription, BoardMember)
from nagare import i18n
from nagare.ajax import py2js


@presentation.render_for(Board, model="menu")
def render_Board_menu(self, h, comp, *args):
    with h.div(class_='navbar', id='boardNavbar'):
        with h.div(class_='navActions', id='boardActions'):
            h << h.a(self.icons['preferences']).action(
                lambda: self.popin.call(
                    popin.Popin(
                        component.Component(
                            BoardConfig(self)
                        ),
                        "edit"
                    )
                )
            )

            if security.has_permissions('edit', self):
                h << self.add_list_overlay
                h << self.edit_description_overlay

            h << h.a(self.icons['export']).action(self.export)

            h << h.a(self.icons['history']).action(
                lambda: self.popin.call(
                    popin.Popin(
                        component.Component(
                            notifications.ActionLog(self)
                        ),
                        'history'
                    )
                )
            )

            if security.has_permissions('manage', self):
                onclick = 'return confirm("%s")' % _("This board will be archived. Are you sure?")
                h << h.a(self.icons['archive'], onclick=onclick).action(self.archive_board)
            else:
                h << h.a(self.icons['leave'], onclick='return confirm("%s")' %
                         _("You won't be able to access this board anymore. Are you sure you want to leave it anyway?")).action(self.leave)

        kw = {'onclick': "YAHOO.kansha.app.toggleMenu('boardNavbar')"}
        with h.div(class_="tab collapse", **kw):
            h << h.a('Board', title='Board', id="boardTab")
    return h.root


@presentation.render_for(Board)
def render_Board(self, h, comp, *args):
    """Main board renderer"""

    h.head.javascript_url('js/jquery-searchinput/jquery.searchinput.js')
    h.head.javascript_url('js/debounce.js')
    h.head.css_url('js/jquery-searchinput/styles/jquery.searchinput.min.css')
    h.head.javascript('searchinput', "jQuery(document).ready(function ($) {$('#search').searchInput();});")
    h << self.title.render(h, 'tabname')
    security.check_permissions('view', self)
    if security.has_permissions('edit', self):
        h << comp.render(h, "menu")

    # TODO: Remove this popin
    h << self.popin.render(h.AsyncRenderer())

    background_image_url = self.background_image_url
    background_image_position = self.background_image_position

    if background_image_url:
        styles = {'repeat': 'background:url(%s) repeat' % background_image_url,
                  'cover': 'background:url(%s) no-repeat; background-size:cover' % background_image_url}
        style = styles[background_image_position]
    else:
        style = ''

    with h.div(class_='board', style=style):
        with h.div(class_='header'):
            h << self.title.render(h.AsyncRenderer())
            h << comp.render(h, 'switch')
        with h.div(class_='bbody'):
            h << comp.render(h.AsyncRenderer(), self.model)
    return h.root


@presentation.render_for(Board, 'search_results')
def render_Board_search_results(self, h, comp, *args):
    h << h.script('YAHOO.kansha.app.highlight_cards(%s);' % ajax.py2js(list(self.card_matches), h))
    h << comp.render(h, 'num_matches')
    return h.root


@presentation.render_for(Board, 'num_matches')
def render_Board_num_matches(self, h, comp, *args):
    if self.card_matches:

        if None in self.card_matches:
            h << h.span(i18n._(u'No matches'), class_='nomatches')
        else:
            n = len(self.card_matches)
            h << (i18n._N(u'%d match', u'%d matches', n) % n)
    else:
        h << u' '
    return h.root


@presentation.render_for(Board, 'switch')
def render_Board_item(self, h, comp, *args):
    with h.div(id='switch_zone'):
        if self.model == 'columns':
            search_cb = ajax.Update(
                            action=self.search,
                            component_to_update='show_results',
                            render=lambda renderer: comp.render(renderer, 'search_results')
                        ).generate_action(1, h).replace('this', 'elt')
            oninput = 'debounce(this, function(elt) { %s; }, 500)' % search_cb
            with h.div(id_='show_results'):
                h << comp.render(h, 'num_matches')
            if self.card_matches:
                if None in self.card_matches:
                    klass = 'nomatches'
                else:
                    klass = 'highlight'
            else:
                klass = ''
            h << h.input(type='text', id_='search', placeholder=_(u'search'),
                         value=self.last_search,
                         oninput=oninput,
                         class_=klass)
            #h << h.a(h.i(class_='icon-search', title=_('search')), class_='btn unselected')
            h << h.SyncRenderer().a(h.i(class_='icon-calendar'), title=_('Calendar mode'), class_='btn unselected').action(self.switch_view)
            h << h.SyncRenderer().a(h.i(class_='icon-th-list'), title=_('Board mode'), class_='btn disabled')
        else:
            h << h.SyncRenderer().a(h.i(class_='icon-calendar'), title=_('Calendar mode'), class_='btn disabled')
            h << h.SyncRenderer().a(h.i(class_='icon-th-list'), title=_('Board mode'), class_='btn unselected').action(self.switch_view)

    return h.root


@presentation.render_for(Board, 'item')
def render_Board_item(self, h, comp, *args):
    def answer():
        comp.answer(self.data.id)

    url = self.data.url
    with h.li(class_="row-fluid"):
        with h.a(self.data.title, href=url, class_="boardItemLabel").action(answer):
            if self.data.description:
                h << {'data-tooltip': self.data.description}
        h << {'onmouseover': """YAHOO.kansha.app.highlight(this, 'members', false);
                                YAHOO.kansha.app.highlight(this, 'archive', false);
                                YAHOO.kansha.app.highlight(this, 'leave', false);""",
              'onmouseout': """YAHOO.kansha.app.highlight(this, 'members', true);
                               YAHOO.kansha.app.highlight(this, 'archive', true);
                               YAHOO.kansha.app.highlight(this, 'leave', true);"""}

        h << self.comp_members.render(h.AsyncRenderer(), 'members')

        if security.has_permissions('manage', self):
            h << h.a(class_='archive', title=_(u'Archive this board')).action(self.archive_board)
        else:
            h << h.a(class_='leave',
                     title=_(u'Leave this board'),
                     onclick='return confirm("%s")' % _("You won't be able to access this board anymore. Are you sure you want to leave it anyway?")
                     ).action(self.leave)
    return h.root


@presentation.render_for(Board, model="archived_item")
def render_Board_archived_item(self, h, comp, *args):
    with h.li(class_="row-fluid"):
        h << h.a(self.data.title, href='#', class_="boardItemLabel")

        h << {'onmouseover': """YAHOO.kansha.app.highlight(this, 'delete', false);
                                YAHOO.kansha.app.highlight(this, 'restore', false);""",
              'onmouseout': """YAHOO.kansha.app.highlight(this, 'delete', true);
                               YAHOO.kansha.app.highlight(this, 'restore', true);"""}

        if security.has_permissions('manage', self):
            onclick = 'return confirm("%s")' % _("This board will be destroyed. Are you sure?")
            h << h.a(class_='delete', title=_(u'Delete this board'), onclick=onclick).action(self.delete)
            h << h.a(class_='restore', title=_(u'Restore this board')).action(self.restore_board)
    return h.root


@presentation.render_for(Board, model='members')
def render_Board_members(self, h, comp, *args):
    """Member section view for card

    First "add user" icons,
    Then icon "more user" if necessary
    And at the end member icons
    """
    reload_board = h.a.action(ajax.Update(render='members', action=self.update_members)).get('onclick')
    h << h.script("""YAHOO.kansha.app.hideOverlay();YAHOO.kansha.reload_boarditems['%s']=function() {%s}""" % (self.id, reload_board))

    with h.div(class_='members'):
        if security.has_permissions('Add Users', self):
            h << h.div(self.overlay_add_members, class_='add')
        if len(self.all_members) > self.max_shown_members:
            h << h.div(self.see_all_members, class_='more wide')
        h << h.div(self.see_all_members_compact, class_='more compact')
        with h.span(class_='wide'):
            for m in self.all_members[:self.max_shown_members]:
                h << m.on_answer(self.remove_member).render(h, 'overlay')
    return h.root


@presentation.render_for(Board, "members_list_overlay")
def render_Board_members_list_overlay(self, h, comp, *args):
    """Overlay to list all members"""
    h << h.h2(_('All members'))
    with h.form:
        with h.div(class_="members"):
            h << [m.on_answer(comp.answer).render(h) for m in self.all_members]
    return h.root


@presentation.render_for(Board, "add_member_overlay")
def render_Board_add_member_overlay(self, h, comp, *args):
    """Overlay to add member"""
    h << h.h2(_('Invite members'))
    friends = self.get_friends(security.get_user())
    if friends:
        with h.div(class_="favorites"):
            h << h.h3(_('Favorites'))
            with h.ul():
                h << h.li([f.on_answer(lambda email: self.invite_members([email])) for f in friends])
    with h.div(class_="members search"):
        h << self.new_member.on_answer(self.invite_members)

    return h.root


@presentation.render_for(Icon)
def render_Icon(self, h, comp, *args):
    if self.title is not None:
        h << h.i(
            self.title, class_=self.icon, title=self.title, alt=self.title)
    else:
        h << h.i(class_=self.icon)
    return h.root


@presentation.render_for(NewBoard)
@security.permissions('create_board')
def render_NewBoard(self, h, comp, *args):
    """Render board creator"""
    title = var.Var()
    buttons_id = h.generate_id()
    user = security.get_user()
    with h.form:
        kw = {"onfocus": ("YAHOO.kansha.app.show('%s', true);"
                          "YAHOO.util.Dom.addClass(this, 'expanded');"
                          ) % buttons_id, }
        h << h.input(type='text', placeholder=_(
            'Create a new board'), class_='new-board-name', **kw).action(title)
        with h.div(id=buttons_id, class_="hidden"):
            h << h.button(_('Add'),
                          class_='btn btn-primary btn-small').action(lambda: self.create_board(comp, title(), user))
            h << ' '
            h << h.button(
                _('Cancel'), class_='btn btn-small').action(comp.answer)
    return h.root


@presentation.render_for(Board, 'calendar')
def render_Board_columns(self, h, comp, *args):
    h.head.css_url('js/fullcalendar-2.2.6/fullcalendar.min.css')
    h.head.javascript_url('js/moment.js')
    h.head.javascript_url('js/fullcalendar-2.2.6/fullcalendar.min.js')
    h.head.css('mont-color', '.fc-toolbar h2 {color: %s}' % (self.title_color if self.title_color else '#5C5C5C'))
    lang = security.get_user().get_locale().language
    if lang != 'en':
        h.head.javascript_url('js/fullcalendar-2.2.6/lang/%s.js' % lang)

    with h.div(id='viewport-wrapper'):
        with h.div(class_='clearfix', id='viewport'):
            h << h.div(id='calendar')
            display_week_numbers = security.get_user().display_week_numbers
            h << h.script("""YAHOO.kansha.app.create_board_calendar($('#calendar'), %s)""" % py2js(display_week_numbers))
    for column in self.columns:
        h << column.render(h, 'calendar')
    return h.root


@presentation.render_for(Board, 'columns')
def render_Board_columns(self, h, comp, *args):
    """Render viewport containing the columns"""
    update_if_version_mismatch = lambda renderer: comp.render(renderer, 'columns') if self.increase_version() else ''

    with h.div(id='viewport-wrapper'):
        with h.div(class_='clearfix', id='viewport'):

            # On cards drag and drop
            action = ajax.Update(action=self.update_card_position, render=update_if_version_mismatch)
            action = '%s;_a;%s=' % (h.add_sessionid_in_url(sep=';'), action._generate_replace(1, h))
            h.head.javascript(h.generate_id(), '''function _send_card_position(data) {
                nagare_getAndEval('%s' + YAHOO.lang.JSON.stringify(data));
            }''' % action)

            # On columns drag and drop
            action = ajax.Update(action=self.update_column_position, render=update_if_version_mismatch)
            action = '%s;_a;%s=' % (h.add_sessionid_in_url(sep=';'), action._generate_replace(1, h))
            h.head.javascript(h.generate_id(), '''function _send_column_position(data) {
                nagare_getAndEval('%s' + YAHOO.lang.JSON.stringify(data));
            }''' % action)

            # Create the reload_columns function used when we need to reload
            # the columns from javascript
            reload_board = h.a.action(ajax.Update()).get('onclick').replace('return', "")
            h.head.javascript(h.generate_id(), """function reload_columns(){%s}""" % reload_board)

            increase_version = h.a.action(ajax.Update(render=update_if_version_mismatch))
            h.head.javascript(h.generate_id(), """function increase_version() {%s}""" % increase_version.get('onclick'))

            # Render columns
            with h.div(id='lists', class_='row'):
                h << h.div(' ', id='dnd-frame')
                for column in self.columns:
                    model = None if not security.has_permissions('edit', self) else column.model or 'dnd'
                    on_answer = lambda v, column = column: column.becomes(self.delete_column(v))
                    h << column.on_answer(on_answer).render(h, model)

            # Call columns resize
            h << h.script('YAHOO.kansha.app.columnsResize();YAHOO.kansha.app.refreshCardsCounters();')
    return h.root


@presentation.render_for(BoardTitle)
def render_BoardTitle(self, h, comp, *args):
    """Render the title of the associated object"""
    kw = {'onmouseover': "YAHOO.kansha.app.tooltip(this, %s)" % json.
          dumps(self.parent.get_description())}
    with h.div(class_='boardTitle', id='board-title', **kw):
        a = h.a(self.text, style="color:%s" % self.parent.title_color)
        if security.has_permissions('edit', self):
            a.action(comp.answer)
        h << a
    return h.root


@presentation.render_for(BoardTitle, model='edit')
def render_BoardTitle_edit(next_method, self, h, comp, *args):
    """Render the title of the associated object"""
    with h.div(class_='boardTitle'):
        next_method(self, h, comp, *args)
    return h.root


@presentation.render_for(BoardDescription)
def render_BoardDescription(self, h, comp, *args):
    """Render description component in edit mode"""
    text = var.Var(self.text)
    with h.form(class_='description-form'):
        txt_id, btn_id = h.generate_id(), h.generate_id()
        h << h.label(_(u'Description'), for_=txt_id)
        ta = h.textarea(text(), id_=txt_id).action(text)
        if not security.has_permissions('edit', self):
            ta(disabled='disabled')
        h << ta
        with h.div:
            if security.has_permissions('edit', self):
                h << h.button(_('Save'), class_='btn btn-primary btn-small',
                              id=btn_id).action(remote.Action(lambda: self.change_text(text())))
                h << ' '
                h << h.button(
                    _('Cancel'), class_='btn btn-small').action(remote.Action(lambda: self.change_text(None)))

        h.head.javascript(h.generate_id(),
                          'YAHOO.kansha.app.addCtrlEnterHandler'
                          '(%r, %r)' % (txt_id, btn_id))

    return h.root


@presentation.render_for(BoardConfig)
def render_BoardConfig(self, h, comp, *args):
    return h.root


@presentation.render_for(BoardConfig, model="edit")
def render_BoardConfig_edit(self, h, comp, *args):
    """Render the board configuration panel"""
    h << h.h2(_(u'Board configuration'))
    with h.div(class_='row-fluid'):
        with h.div(class_='span8'):
            h << self.content
        with h.div(class_='span4'):
            with h.ul(class_='nav nav-pills nav-stacked'):
                h << h.li(_('Menu'), class_='nav-header')
                for title, _o in self.menu:
                    with h.li(class_='active' if title == self.selected else ''):
                        h << h.a(title).action(
                            lambda title=title: self.select(title))

    h << h.script('YAHOO.kansha.app.hideOverlay();')
    h << h.script("YAHOO.util.Event.onDOMReady(function() {YAHOO.util.Dom.setStyle('mask', 'display', 'block')})")
    return h.root


@presentation.render_for(BoardLabels, model='menu')
def render_BoardLabels_menu(self, h, comp, *args):
    """Render the link leading to the label configuration"""
    h << h.a(_('Labels')).action(comp.answer)
    return h.root


@presentation.render_for(BoardLabels)
@presentation.render_for(BoardLabels, model='edit')
def render_BoardLabels_edit(self, h, comp, *args):
    """Render the labels configuration panel"""
    h << h.div(h.i(class_='icon-tag'), _(u'Card labels'), class_='panel-section')
    with h.ul(class_='unstyled board-labels clearfix'):
        for title, label in self.labels:
            with h.li(class_='row-fluid'):
                with h.div(class_='span7'):
                    with h.div(class_='label-title'):
                        h << title.on_answer(lambda a, title=title: title.
                                             call(model='edit')).render(h.AsyncRenderer())
                with h.div(class_='span5'):
                    with h.div(class_='label-color'):
                        h << label
    return h.root


@presentation.render_for(BoardWeights, model='menu')
def render_boardweights_menu(self, h, comp, *args):
    """Render the link leading to the weights configuration"""
    h << h.a(_('Weights')).action(comp.answer)
    return h.root


@presentation.render_for(BoardWeights)
@presentation.render_for(BoardWeights, model='edit')
def render_boardweights_edit(self, h, comp, *args):
    """Render the weights configuration panel"""
    h << h.div(h.i(class_='icon-weighting'), _(u'Weighting cards'), class_='panel-section')
    h << h.p(_(u'Activate cards weights'))
    with h.form:
        with h.div(class_='btn-group'):
            if self._changed():
                h << h.script('reload_columns()')
                self._changed(False)

            active = 'active btn-primary' if self.board.weighting_cards == WEIGHTING_OFF else ''

            action = h.a.action(self.deactivate_weighting).get('onclick')
            onclick = "if (confirm(\"%(confirm_msg)s\")){%(action)s;}return false;"
            onclick = onclick % dict(action=action, confirm_msg=_(u'All affected weights will be reseted. Are you sure?'))

            h << h.a(_('Disabled'), class_='btn %s' % active, onclick=onclick)

            action = h.a.action(lambda: self.activate_weighting(WEIGHTING_FREE)).get('onclick')
            onclick = "if (confirm(\"%(confirm_msg)s\")){%(action)s;}return false;"
            onclick = onclick % dict(action=action, confirm_msg=_(u'All affected weights will be reseted. Are you sure?'))

            active = 'active btn-primary' if self.board.weighting_cards == WEIGHTING_FREE else ''
            h << h.button(_('Free integer'), title=i18n._('Card weights can be any integer'), class_='btn %s' % active, onclick=onclick)

            action = h.a.action(lambda: self.activate_weighting(WEIGHTING_LIST)).get('onclick')
            onclick = "if (confirm(\"%(confirm_msg)s\")){%(action)s;}return false;"
            onclick = onclick % dict(action=action, confirm_msg=_(u'All affected weights will be reseted. Are you sure?'))

            active = 'active btn-primary' if self.board.weighting_cards == WEIGHTING_LIST else ''
            h << h.button(_('Integer sequence'), title=i18n._('Choosen within a sequence of integers'), class_='btn %s' % active, onclick=onclick)

    if self.board.weighting_cards == WEIGHTING_LIST:
        h << h.p(i18n._('Enter a sequence of integers'))
        h << self._weights_editor

    return h.root


@presentation.render_for(WeightsSequenceEditor)
def render_weightssequenceeditor(self, h, comp, model):
    with h.form(class_='weights-form'):
        kw = {'disabled': 'disabled'}
        if not self.weights():
            kw["placeholder"] = "10,20,30"
        h << h.input(value=self.weights(), type='text', **kw).action(self.weights).error(self.weights.error)
        h << h.button(_('Edit'), class_='btn btn-primary btn-small').action(lambda: comp.call(self, 'edit'))
    return h.root


@presentation.render_for(WeightsSequenceEditor, 'edit')
def render_weightssequenceeditor_edit(self, h, comp, model):

    def answer():
        if self.commit():
            comp.call(self, None)

    with h.form(class_='weights-form'):
        kw = {}
        if not self.weights():
            kw["placeholder"] = "10,20,30"
        h << h.input(value=self.weights(), type='text', **kw).action(self.weights).error(self.weights.error)
        h << h.button(_('Save'), class_='btn btn-primary btn-small').action(answer)
    return h.root


@presentation.render_for(BoardProfile)
def render_BoardProfile(self, h, comp, *args):
    """Render the board profile form"""
    if security.has_permissions('manage', self.board):
        h << h.div(h.i(class_='icon-visibility'),
                   _(u'Visibility'), class_='panel-section')
        h << h.p(_(u'Choose whether the board is private or public.'))
        with h.form:
            with h.div(class_='btn-group'):
                active = 'active btn-primary' if self.board.visibility == BOARD_PRIVATE else ''
                h << h.button(_('Private'), class_='btn %s' % active).action(
                    lambda: self.board.set_visibility(BOARD_PRIVATE))
                active = 'active btn-primary' if self.board.visibility == BOARD_PUBLIC else ''
                h << h.button(_('Public'), class_='btn %s' % active).action(
                    lambda: self.board.set_visibility(BOARD_PUBLIC))

        h << h.div(h.i(class_='icon-comment'), _(u'Comments'), class_='panel-section')
        h << h.p(_('Commenting allows members to make short messages on cards. You can enable or disable this feature.'))
        with h.form:
            with h.div(class_='btn-group'):
                active = 'active btn-primary' if self.board.comments_allowed == COMMENTS_OFF else ''
                h << h.button(_('Disabled'), class_='btn %s' % active).action(
                    lambda: self.allow_comments(COMMENTS_OFF))
                active = 'active btn-primary' if self.board.comments_allowed == COMMENTS_MEMBERS else ''
                h << h.button(_('Members'), class_='btn %s' % active).action(
                    lambda: self.allow_comments(COMMENTS_MEMBERS))
                kw = {} if self.board.visibility == BOARD_PUBLIC else {
                    "disabled": "disabled"}
                active = 'active btn-primary' if self.board.comments_allowed == COMMENTS_PUBLIC else ''
                h << h.button(_('Public'), class_='btn %s' % active, **kw).action(
                    lambda: self.allow_comments(COMMENTS_PUBLIC))

        h << h.div(h.i(class_='icon-vote'), _(u'Votes'), class_='panel-section')
        h << h.p(_(u'Allow votes'))
        with h.form:
            with h.div(class_='btn-group'):
                active = 'active btn-primary' if self.board.votes_allowed == VOTES_OFF else ''
                h << h.button(_('Disabled'), class_='btn %s' %
                              active).action(lambda: self.allow_votes(VOTES_OFF))
                active = 'active btn-primary' if self.board.votes_allowed == VOTES_MEMBERS else ''
                h << h.button(_('Members'), class_='btn %s' % active).action(
                    lambda: self.allow_votes(VOTES_MEMBERS))
                kw = {} if self.board.visibility == BOARD_PUBLIC else {
                    "disabled": "disabled"}
                active = 'active btn-primary' if self.board.votes_allowed == VOTES_PUBLIC else ''
                h << h.button(_('Public'), class_='btn %s' % active,
                              **kw).action(lambda: self.allow_votes(VOTES_PUBLIC))

        h << h.div(h.i(class_='icon-archive'), _(u'Archive'), class_='panel-section')
        h << h.p(_(u'View archive column'))
        with h.form:
            with h.div(class_='btn-group'):
                if self._changed():
                    h << h.script('reload_columns()')
                    self._changed(False)

                active = 'active btn-primary' if self.board.archive else ''
                h << h.button(_('Show'), class_='btn %s' % active).action(lambda: self.set_archive(1))
                active = 'active btn-primary' if not self.board.archive else ''
                h << h.button(_('Hide'), class_='btn %s' % active).action(lambda: self.set_archive(0))

    h << h.div(h.i(class_='icon-notify'), _(u'Notifications'), class_='panel-section')
    h << h.p(_(u'You will be notified by email of changes made in this board to cards'))
    with h.form:
        with h.div(class_='btn-group'):
            active = 'active btn-primary' if self.notifications_allowed == notifications.NOTIFY_OFF else ''
            h << h.button(_('None'), class_='btn %s' % active).action(self.allow_notifications, notifications.NOTIFY_OFF)
            active = 'active btn-primary' if self.notifications_allowed == notifications.NOTIFY_MINE else ''
            h << h.button(_('Affected to me'), class_='btn %s' % active).action(self.allow_notifications, notifications.NOTIFY_MINE)
            active = 'active btn-primary' if self.notifications_allowed == notifications.NOTIFY_ALL else ''
            h << h.button(_('All'), class_='btn %s' % active).action(self.allow_notifications, notifications.NOTIFY_ALL)
    return h.root


@presentation.render_for(BoardMember)
def render_BoardMember(self, h, comp, *args):
    if security.has_permissions('manage', self.board):
        return self.user.on_answer(self.dispatch).render(h, model='%s' % self.role)
    else:
        def dispatch(answer):
            self.dispatch(answer)
            comp.answer()
        return h.div(self.user.on_answer(dispatch).render(h), class_='member')


@presentation.render_for(BoardMember, model="overlay")
def render_BoardMember_overlay(self, h, comp, *args):
    if security.has_permissions('manage', self.board):
        return self.user.on_answer(self.dispatch).render(h, model='overlay-%s' % self.role)
    else:
        member = self.user.render(h, "avatar")
        member.attrib.update({'class': 'miniavatar unselectable'})
        return member


@presentation.render_for(BoardBackground, model='menu')
def render_board_background_menu(self, h, comp, *args):
    """Render the link leading to the background configuration"""
    h << h.a(_('Background image')).action(comp.answer)
    return h.root


@presentation.render_for(BoardBackground)
@presentation.render_for(BoardBackground, model='edit')
def render_board_background_edit(self, h, comp, *args):
    """Render the background configuration panel"""
    h << h.div(_(u'Background image'), class_='panel-section')
    with h.div(class_='row-fluid'):
        with h.div(class_='span6'):
            def set_background(img):
                self.board.set_background_image(img)
                self._changed(True)
            v_file = var.Var()
            submit_id = h.generate_id("attach_submit")
            input_id = h.generate_id("attach_input")
            h << h.label((h.i(class_='icon-file icon-grey'),
                          _("Choose an image")), class_='btn btn-small', for_=input_id)
            with h.form:
                h << h.script(u'''
            function valueChanged(e) {
                if (YAHOO.kansha.app.checkFileSize(this, %(max_size)s)) {
                    YAHOO.util.Dom.get('%(submit_id)s').click();
                } else {
                    alert('%(error)s');
                }
            }

            YAHOO.util.Event.onDOMReady(function() {
                YAHOO.util.Event.on('%(input_id)s', 'change', valueChanged);
            });''' % {'max_size': self.board.background_max_size,
                      'input_id': input_id,
                      'submit_id': submit_id,
                      'error': _(u'Max file size exceeded')})
                h << h.input(id=input_id, style="position:absolute;left:-1000px;", type="file", name="file",
                             multiple="multiple", maxlength="100",).action(v_file)
                h << h.input(style="position:absolute;left:-1000px;", id=submit_id, type="submit").action(
                    lambda: set_background(v_file()))
        with h.div(class_='span5'):
            def reset_background():
                self.board.set_background_image(None)
                self._changed(True)
            h << _('or') << ' '
            h << h.a(_('Reset background')).action(reset_background)
    with h.div(class_='row-fluid'):
        with h.span(class_='span12 text-center'):
            h << component.Component(self.board, model='background_image')

    h << h.div(_(u'Board title color'), class_='panel-section')
    with h.div(class_='row-fluid'):
        with h.div(class_='span6'):
            h << comp.render(h, model='title-color-edit')
        with h.div(class_='span5'):
            def reset_color():
                self.board.set_title_color(None)
                self._changed(True)
            h << _('or') << ' '
            h << h.a(_('Reset to default color')).action(reset_color)
    return h.root


@presentation.render_for(Board, model='background_image')
def render_board_background_image(self, h, comp, *args):
    fileid = self.data.background_image
    try:
        metadata = self.assets_manager.get_metadata(fileid)
        src = self.assets_manager.get_image_url(fileid, 'medium')
        src += '?r=' + h.generate_id()
        return h.img(title=metadata['filename'], alt=metadata['filename'], src=src)
    except Exception:
        return _(u'No background selected')


@presentation.render_for(BoardBackground, model='title-color-edit')
def render_board_background_title_color_edit(self, h, comp, *args):
    """Edit the label color"""
    # If label changed reload columns
    if self._changed():
        h.head.javascript(h.generate_id(), "YAHOO.kansha.app.set_title_color('%s')" % self.board.title_color or u'')
        image_url = self.board.background_image_url or ''
        image_position = self.board.background_image_position
        h.head.javascript(h.generate_id(), "YAHOO.kansha.app.set_board_background_image('%s', '%s')" % (image_url,
                                                                                                       image_position))
        self._changed(False)
    h << component.Component(overlay.Overlay(lambda r: comp.render(r, model='title-color'),
                                             lambda r: comp.render(r,
                                                                   model='title-color-overlay'),
                                             dynamic=False,
                                             title=_('Change color')))
    return h.root


@presentation.render_for(BoardBackground, model='title-color')
def render_board_background_title_color(self, h, comp, *args):
    style = 'background-color:%s' % (self.board.title_color or u'')
    h << h.span(class_='board-title-color', style=style, data_tooltip=json.dumps(self.board.data.id))
    return h.root


@presentation.render_for(BoardBackground, model='title-color-overlay')
def render_board_background_title_color_overlay(self, h, comp, *args):
    """Color chooser contained in the overlay body"""
    def set_color(color):
        self.board.set_title_color(color)
        self._changed(True)

    v = var.Var(self.board.title_color)
    i = h.generate_id()
    h << h.div(id=i, class_='label-color-picker clearfix')
    with h.form:
        h << h.input(type='hidden', value=v(), id='%s-hex-value' % i).action(v)
        h << h.button(_('Save'), class_='btn btn-primary btn-small').action(
            ajax.Update(action=lambda v=v: set_color(v())))
        h << ' '
        h << h.button(_('Cancel'), class_='btn btn-small').action(lambda: None)
    h << h.script("YAHOO.kansha.app.addColorPicker(%r)" % i)
    return h.root
