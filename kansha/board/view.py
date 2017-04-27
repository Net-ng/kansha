# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from nagare.i18n import _, _N, _L
from nagare import ajax, component, presentation, security, var

from kansha import notifications
from kansha.toolbox import overlay, remote
from kansha.board.boardconfig import WeightsSequenceEditor

from .boardsmanager import BoardsManager
from .comp import (Board, BoardDescription, BoardMember,
                   Icon)
from .comp import (BOARD_PRIVATE, BOARD_PUBLIC, BOARD_SHARED,
                   COMMENTS_OFF, COMMENTS_PUBLIC, COMMENTS_MEMBERS,
                   VOTES_OFF, VOTES_PUBLIC, VOTES_MEMBERS,
                   WEIGHTING_FREE, WEIGHTING_LIST, WEIGHTING_OFF)
from .boardconfig import BoardBackground, BoardConfig, BoardLabels, BoardProfile, BoardWeights

VISIBILITY_ICONS = {
    BOARD_PRIVATE: 'icon-lock',
    BOARD_PUBLIC: 'icon-unlocked',
    BOARD_SHARED: 'icon-earth'
}

BACKGROUND_POSITIONS = [
    ('fill', _L(u"fill")),
    ('fit', _L(u"fit")),
    ('stretch', _L(u"stretch")),
    ('tile', _L(u"tile")),
    ('center', _L(u"center"))
]


@presentation.render_for(Board, model="menu")
def render_Board_menu(self, h, comp, *args):
    with h.div(class_='nav-menu', onclick='YAHOO.kansha.app.toggleMainMenu(this)'):
        with h.ul(class_='actions large'):
            h << h.li(h.a(self.icons['preferences']).action(self.show_preferences))
            if security.has_permissions('edit', self):
                h << h.li(h.a(self.icons['add_list']).action(self.add_list))
                h << h.li(h.a(self.icons['edit_desc']).action(self.edit_description))
            if security.has_permissions('manage', self):
                h << h.li(h.a(self.icons['save_template']).action(self.save_template, comp))

            h << h.li(h.SyncRenderer().a(self.icons['export']).action(self.export))
            h << h.li(h.a(self.icons['history']).action(self.show_actionlog))

            if security.has_permissions('manage', self):
                h << h.li(h.SyncRenderer().a(
                    self.icons['archive'],
                    onclick=(
                        'return confirm(%s)' %
                        ajax.py2js(
                            _("This board will be archived. Are you sure?")
                        ).decode('UTF-8')
                    )
                ).action(self.archive, comp))
            else:
                h << h.li(h.SyncRenderer().a(
                    self.icons['leave'],
                    onclick=(
                        "return confirm(%s)" %
                        ajax.py2js(
                            _("You won't be able to access this board anymore. Are you sure you want to leave it anyway?")
                        ).decode('UTF-8')
                    )
                ).action(self.leave, comp))

        h << h.span(_(u'Board'), class_="menu-title", id='board-nav-menu')
    h << self.modal
    return h.root


@presentation.render_for(Board)
def render_Board(self, h, comp, *args):
    """Main board renderer"""
    security.check_permissions('view', self)
    self.refresh_on_version_mismatch()
    self.card_filter.reload_search()
    h.head.css_url('css/themes/board.css?v=2c')
    h.head.css_url('css/themes/%s/board.css?v=2c' % self.theme)

    title = '%s - %s' % (self.get_title(), self.app_title)
    h.head << h.head.title(title)
    if security.has_permissions('edit', self):
        h << comp.render(h.AsyncRenderer(), "menu")

    with h.div(class_='board'):
        if self.background_image_url:
            h << {'class': 'board ' + self.background_image_position,
                  'style': 'background-image:url(%s)' % self.background_image_url}
        with h.div(class_='header'):
            with h.div(class_='board-title', style='color: %s' % self.title_color):
                h << self.title.render(h.AsyncRenderer(), 0 if security.has_permissions('edit', self) else 'readonly')
            h << comp.render(h, 'switch')
        with h.div(class_='bbody'):
            h << comp.render(h.AsyncRenderer(), self.model)
    return h.root


@presentation.render_for(Board, 'switch')
def render_Board_item(self, h, comp, *args):

    with h.div(id='switch_zone'):
        if self.model == 'columns':
            # card search
            h << self.search_input
            # Switch view
            h << h.SyncRenderer().a(
                h.i(class_='icon-calendar'),
                title=_('Calendar mode'),
                class_='btn icon-btn ',
                style='color: %s' % self.title_color).action(self.switch_view)
            h << h.SyncRenderer().a(
                h.i(class_='icon-list'),
                title=_('Board mode'),
                class_='btn icon-btn disabled selected',
                style='color: %s' % self.title_color)
        else:
            h << h.SyncRenderer().a(
                h.i(class_='icon-calendar'),
                title=_('Calendar mode'),
                class_='btn icon-btn disabled selected',
                style='color: %s' % self.title_color)
            h << h.SyncRenderer().a(
                h.i(class_='icon-list'),
                title=_('Board mode'),
                class_='btn icon-btn',
                style='color: %s' % self.title_color).action(self.switch_view)

    return h.root


@presentation.render_for(Board, 'item')
def render_Board_item(self, h, comp, *args):
    def answer():
        comp.answer(self.data.id)

    url = self.data.url
    with h.li:
        h << h.SyncRenderer().a(
            h.i(' ', class_=VISIBILITY_ICONS[self.data.visibility]),
            self.data.title,
            href=url, class_="boardItemLabel", title=self.data.description)

        with h.div(class_='actions'):
            h << self.comp_members.render(h, 'members')

            if security.has_permissions('manage', self):
                h << h.a(
                    h.i(class_='ico-btn icon-box-add'),
                    class_='archive',
                    title=_(u'Archive "%s"') % self.data.title
                ).action(self.archive, comp)
            elif security.has_permissions('leave', self):
                onclick = 'return confirm("%s")' % _("You won't be able to access this board anymore. Are you sure you want to leave it anyway?")
                h << h.SyncRenderer().a(
                    h.i(class_='ico-btn icon-exit'),
                    class_='leave',
                    title=_(u'Leave "%s"') % self.data.title,
                    onclick=onclick
                ).action(self.leave, comp)
            else:
                # place holder for alignment and for future feature 'request membership'
                h << h.a(h.i(class_='ico-btn icon-user-check'), style='visibility:hidden')
    return h.root


@presentation.render_for(Board, 'redirect')
def render_Board_redirect(self, h, comp, model):
    h << h.script('window.location.href="%s"' % self.data.url)
    return h.root


@presentation.render_for(Board, model="archived_item")
def render_Board_archived_item(self, h, comp, *args):
    with h.li(class_='archived-item'):
        h << h.span(
            h.i(' ', class_=VISIBILITY_ICONS[self.data.visibility]),
            self.data.title,
            href='#', class_="boardItemLabel")

        if security.has_permissions('manage', self):
            with h.div(class_='actions'):
                onclick = 'return confirm("%s")' % _("This board will be destroyed. Are you sure?")
                h << h.SyncRenderer().a(
                    h.i(class_='ico-btn icon-bin'),
                    class_='delete',
                    title=_(u'Delete "%s"') % self.data.title,
                    onclick=onclick
                ).action(self.delete_clicked, comp)
                h << h.a(
                    h.i(class_='ico-btn icon-box-remove'),
                    class_='restore',
                    title=_(u'Restore "%s"') % self.data.title
                ).action(self.restore, comp)
    return h.root


@presentation.render_for(Board, model='members')
def render_Board_members(self, h, comp, *args):
    """Member section view for card

    First "add user" icons,
    Then icon "more user" if necessary
    And at the end member icons
    """
    with h.div(class_='members'):
        if security.has_permissions('Add Users', self):
            h << h.div(self.overlay_add_members, class_='add')
        if len(self.all_members) > self.MAX_SHOWN_MEMBERS:
            h << h.div(self.see_all_members, class_='more wide')
        h << h.div(self.see_all_members_compact, class_='more compact')
        with h.span(class_='wide'):
            for m in self.all_members[:self.MAX_SHOWN_MEMBERS]:
                h << m.on_answer(self.handle_event, comp).render(h, 'overlay')
    return h.root


@presentation.render_for(Board, "members_list_overlay")
def render_Board_members_list_overlay(self, h, comp, *args):
    """Overlay to list all members"""
    h << h.h2(_('All members'))
    with h.form:
        with h.div(class_="members"):
            h << [m.on_answer(self.handle_event, comp).render(h) for m in self.all_members]
    return h.root


def invite_members(board, application_url, emails):
    board.invite_members(emails, application_url)
    return 'reload_boards();'


@presentation.render_for(Board, "add_member_overlay")
def render_Board_add_member_overlay(self, h, comp, *args):
    """Overlay to add member"""
    h << h.h2(_('Invite members'))
    application_url = h.request.application_url
    with h.div(class_="members search"):
        h << self.new_member.on_answer(invite_members, self, application_url)

    return h.root


@presentation.render_for(Icon)
def render_Icon(self, h, comp, *args):
    if self.title is not None:
        h << h.i(class_=self.icon, title=self.title)
        h << self.title
    else:
        h << h.i(class_=self.icon, title=self.title)
    return h.root


@presentation.render_for(Board, 'calendar')
def render_Board_columns(self, h, comp, *args):
    h.head.css_url('js/fullcalendar-2.2.6/fullcalendar.min.css')
    h.head.javascript_url('js/moment.js')
    h.head.javascript_url('js/fullcalendar-2.2.6/fullcalendar.min.js')
    lang = security.get_user().get_locale().language
    if lang != 'en':
        h.head.javascript_url('js/fullcalendar-2.2.6/lang/%s.js' % lang)

    with h.div(id='viewport-wrapper'):
        with h.div(class_='clearfix', id='viewport'):
            h << h.div(id='calendar')
            h << h.script("""YAHOO.kansha.app.create_board_calendar($('#calendar'), %s)""" % ajax.py2js(True, h))
    for column in self.columns:
        if not column().is_archive:
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
                nagare_getAndEval(%s + YAHOO.lang.JSON.stringify(data));
            }''' % ajax.py2js(action))

            # On columns drag and drop
            action = ajax.Update(action=self.update_column_position, render=update_if_version_mismatch)
            action = '%s;_a;%s=' % (h.add_sessionid_in_url(sep=';'), action._generate_replace(1, h))
            h.head.javascript(h.generate_id(), '''function _send_column_position(data) {
                nagare_getAndEval(%s + YAHOO.lang.JSON.stringify(data));
            }''' % ajax.py2js(action))

            # Create the reload_columns function used when we need to reload
            # the columns from javascript
            reload_board = h.a.action(ajax.Update()).get('onclick').replace('return', "")
            h.head.javascript(h.generate_id(), """function reload_columns(){%s}""" % reload_board)

            increase_version = h.a.action(ajax.Update(render=update_if_version_mismatch))
            h.head.javascript(h.generate_id(), """function increase_version() {%s}""" % increase_version.get('onclick'))

            # Render columns
            visible_cols = len(self.columns) - int(not self.show_archive)
            layout = ''
            if 2 < visible_cols < 6:
                layout = 'list-span-{}'.format(visible_cols)
            elif visible_cols < 3:
                layout = 'list-span-3'

            with h.div(id='lists'):
                if layout:
                    h << {'class': layout}
                h << h.div(' ', id='dnd-frame')
                for column in self.columns:
                    if column().is_archive and not self.show_archive:
                        continue
                    model = 0 if not security.has_permissions('edit', self) else column.model or 'dnd'
                    h << column.on_answer(self.handle_event, comp).render(h, model)
    return h.root


@presentation.render_for(BoardDescription)
def render_BoardDescription(self, h, comp, *args):
    """Render description component in edit mode"""
    h << h.h2(_(u'Edit board description'))
    with h.form(class_='description-form'):
        txt_id, btn_id = h.generate_id(), h.generate_id()
        h << h.label(_(u'Description'), for_=txt_id)
        h << h.textarea(self.description(), id_=txt_id, autofocus=True).action(self.description)
        with h.div(class_='buttons'):
            h << h.button(_('Save'), class_='btn btn-primary', id=btn_id).action(self.commit, comp)
            h << ' '
            h << h.a(_('Cancel'), class_='btn').action(self.cancel, comp)

        h.head.javascript(
            h.generate_id(),
            'YAHOO.kansha.app.addCtrlEnterHandler(%s, %s)' % (
                ajax.py2js(txt_id), ajax.py2js(btn_id)
            )
        )

    return h.root


@presentation.render_for(BoardConfig)
def render_BoardConfig(self, h, comp, *args):
    return comp.render(h.AsyncRenderer(), 'edit')


@presentation.render_for(BoardConfig, model='edit')
def render_BoardConfig_edit(self, h, comp, *args):
    """Render the board configuration panel"""
    h << h.h2(_(u'Board configuration'))
    with h.div(class_='row board-configuration'):
        with h.div(class_='menu'):
            with h.div:
                with h.ul:
                    for id_, item in self.menu.iteritems():
                        with h.li:
                            with h.a.action(lambda id_=id_: self.select(id_)):
                                if id_ == self.selected:
                                    h << {'class': 'active'}
                                h << h.i(class_='icon ' + item.icon)
                                h << h.span(item.label)
        with h.div:
            h << self.content

    h << h.script('YAHOO.kansha.app.hideOverlay();')
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
    with h.div(class_='panel-section'):
        h << h.div(_(u'Card labels'), class_='panel-section-title')
        with h.ul(class_='board-labels clearfix'):
            for title, label in self.labels:
                with h.li:
                    with h.div(class_='label-title'):
                        h << title.render(h.AsyncRenderer())
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
    with h.div(class_='panel-section'):
        h << h.div(_(u'Weighting cards'), class_='panel-section-title')
        h << h.p(_(u'Activate cards weights'))
        with h.form:
            with h.div(class_='btn-group'):
                action = h.a.action(self.activate_weighting, WEIGHTING_OFF).get('onclick')
                if self.board.total_weight() > 0:
                    action = (
                        "if (confirm(%(message)s)){%(action)s;}return false" %
                        {
                            'action': action,
                            'message': ajax.py2js(
                                _(u'All affected weights will be reset. Are you sure?')
                            ).decode('UTF-8')
                        }
                    )
                h << h.a(
                    _('Disabled'),
                    class_='btn %s' % (
                        'active btn-primary'
                        if self.board.weighting_cards == WEIGHTING_OFF
                        else ''
                    ),
                    onclick=action
                )

                h << h.button(
                    _('Free integer'),
                    class_='btn %s' % (
                        'active btn-primary'
                        if self.board.weighting_cards == WEIGHTING_FREE
                        else ''
                    ),
                    onclick=h.a.action(
                        self.activate_weighting, WEIGHTING_FREE
                    ).get('onclick'),
                    title=_('Card weights can be any integer')
                )

                action = h.a.action(self.activate_weighting, WEIGHTING_LIST).get('onclick')
                if self.board.total_weight() > 0:
                    action = (
                        "if (confirm(%(message)s)){%(action)s;}return false" %
                        {
                            'action': action,
                            'message': ajax.py2js(
                                _(u'All affected weights will be reset. Are you sure?')
                            ).decode('UTF-8')
                        }
                    )
                h << h.button(
                    _('Integer sequence'),
                    class_='btn %s' % (
                        'active btn-primary'
                        if self.board.weighting_cards == WEIGHTING_LIST
                        else ''
                    ),
                    onclick=action,
                    title=_('Choosen within a sequence of integers')
                )

        if self.board.weighting_cards == WEIGHTING_LIST:
            h << h.p(_('Enter a sequence of integers'))
            h << self._weights_editor

    return h.root


@presentation.render_for(WeightsSequenceEditor)
def render_weightssequenceeditor_edit(self, h, comp, model):

    with h.form(class_='weights-form'):
        h << h.input(value=self.weights(), type='text').action(self.weights)
        h << h.button(_('Save'), class_='btn btn-primary').action(self.commit)
        if self.weights.error:
            h << h.div(self.weights.error, class_='nagare-error-message')
        elif self.feedback:
            with h.div(class_='success'):
                h << h.i(class_='icon-checkmark')
                h << self.feedback

    return h.root


@presentation.render_for(BoardProfile)
def render_BoardProfile(self, h, comp, *args):
    """Render the board profile form"""
    if security.has_permissions('manage', self.board):
        with h.div(class_='panel-section'):
            h << h.div(_(u'Content Visibility'), class_='panel-section-title')
            h << h.p(_(u'Choose whether the board is private, public (anyone with the URL can view it ) or shared (public + visible on homepages).'))
            with h.form:
                with h.div(class_='btn-group'):
                    active = 'active btn-primary' if self.board.visibility == BOARD_PRIVATE else ''
                    h << h.button(_('Private'), class_='btn %s' % active).action(
                        lambda: self.board.set_visibility(BOARD_PRIVATE))
                    active = 'active btn-primary' if self.board.visibility == BOARD_PUBLIC else ''
                    h << h.button(_('Public'), class_='btn %s' % active).action(
                        lambda: self.board.set_visibility(BOARD_PUBLIC))
                    active = 'active btn-primary' if self.board.visibility == BOARD_SHARED else ''
                    h << h.button(_('Shared'), class_='btn %s' % active).action(
                        lambda: self.board.set_visibility(BOARD_SHARED))

        with h.div(class_='panel-section'):
            h << h.div(_(u'Comments'), class_='panel-section-title')
            h << h.p(_('Commenting allows members to make short messages on cards. You can enable or disable this feature.'))
            with h.form:
                with h.div(class_='btn-group'):
                    active = 'active btn-primary' if self.board.comments_allowed == COMMENTS_OFF else ''
                    h << h.button(_('Disabled'), class_='btn %s' % active).action(
                        lambda: self.allow_comments(COMMENTS_OFF))
                    active = 'active btn-primary' if self.board.comments_allowed == COMMENTS_MEMBERS else ''
                    h << h.button(_('Members'), class_='btn %s' % active).action(
                        lambda: self.allow_comments(COMMENTS_MEMBERS))
                    kw = {} if self.board.is_open else {
                        "disabled": "disabled"}
                    active = 'active btn-primary' if self.board.comments_allowed == COMMENTS_PUBLIC else ''
                    h << h.button(_('Public'), class_='btn %s' % active, **kw).action(
                        lambda: self.allow_comments(COMMENTS_PUBLIC))

        with h.div(class_='panel-section'):
            h << h.div(_(u'Votes'), class_='panel-section-title')
            h << h.p(_(u'Allow votes'))
            with h.form:
                with h.div(class_='btn-group'):
                    active = 'active btn-primary' if self.board.votes_allowed == VOTES_OFF else ''
                    h << h.button(_('Disabled'), class_='btn %s' %
                                  active).action(lambda: self.allow_votes(VOTES_OFF))
                    active = 'active btn-primary' if self.board.votes_allowed == VOTES_MEMBERS else ''
                    h << h.button(_('Members'), class_='btn %s' % active).action(
                        lambda: self.allow_votes(VOTES_MEMBERS))
                    kw = {} if self.board.is_open else {
                        "disabled": "disabled"}
                    active = 'active btn-primary' if self.board.votes_allowed == VOTES_PUBLIC else ''
                    h << h.button(_('Public'), class_='btn %s' % active,
                                  **kw).action(lambda: self.allow_votes(VOTES_PUBLIC))

        with h.div(class_='panel-section'):
            h << h.div(_(u'Archive'), class_='panel-section-title')
            h << h.p(_(u'View archive column'))
            with h.form:
                with h.div(class_='btn-group'):

                    active = 'active btn-primary' if self.board.show_archive else ''
                    h << h.button(_('Show'), class_='btn %s' % active).action(lambda: self.set_archive(1))
                    active = 'active btn-primary' if not self.board.show_archive else ''
                    h << h.button(_('Hide'), class_='btn %s' % active).action(lambda: self.set_archive(0))

    with h.div(class_='panel-section'):
        h << h.div(_(u'Notifications'), class_='panel-section-title')
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
    application_url = h.request.application_url
    if security.has_permissions('manage', self.board):
        return self.user.on_answer(
            lambda action: self.dispatch(action, application_url)
        ).render(h, model='%s' % self.role)
    else:
        return h.div(self.user.render(h), class_='member')


@presentation.render_for(BoardMember, model="overlay")
def render_BoardMember_overlay(self, h, comp, *args):
    application_url = h.request.application_url
    if security.has_permissions('manage', self.board):
        return self.user.on_answer(
            lambda action: self.dispatch(action, application_url)
        ).render(h, model='overlay-%s' % self.role)
    else:
        member = self.user.render(h, "avatar")
        member.attrib.update({'class': 'avatar unselectable'})
        return member


@presentation.render_for(BoardBackground, model='menu')
def render_board_background_menu(self, h, comp, *args):
    return h.a(_('Background image')).action(comp.answer)


@presentation.render_for(BoardBackground)
@presentation.render_for(BoardBackground, model='edit')
def render_board_background_edit(self, h, comp, *args):
    """Render the background configuration panel"""

    with h.div(class_='panel-section'):
        h << h.div(_(u'Background image'), class_='panel-section-title')
        with h.div:
            with h.div:
                v_file = var.Var()
                submit_id = h.generate_id("attach_submit")
                input_id = h.generate_id("attach_input")
                h << h.label((h.i(class_='icon-file-picture'), u' ',
                              _("Choose an image")), class_='btn', for_=input_id)
                with h.form(class_='hidden'):
                    h << h.script(
                        u'''
                function valueChanged(e) {
                    if (YAHOO.kansha.app.checkFileSize(this, %(max_size)s)) {
                        YAHOO.util.Dom.get(%(submit_id)s).click();
                    } else {
                        alert(%(error)s);
                    }
                }

                YAHOO.util.Event.onDOMReady(function() {
                    YAHOO.util.Event.on(%(input_id)s, 'change', valueChanged);
                });''' % {
                            'max_size': ajax.py2js(self.board.background_max_size, h),
                            'input_id': ajax.py2js(input_id, h),
                            'submit_id': ajax.py2js(submit_id, h),
                            'error': ajax.py2js(
                                _(u'Max file size exceeded'), h
                            ).decode('UTF-8')
                        }
                    )
                    h << h.input(id=input_id, class_='hidden', type="file", name="file",
                                 multiple="multiple", maxlength="100",).action(v_file)
                    h << h.input(id=submit_id, class_='hidden', type="submit").action(
                        lambda: self.set_background(v_file()))
                h << ' ' << _('or') << ' '
                h << h.a(_(u'Reset background')).action(self.reset_background)
        with h.p(class_='text-center'):
            h << component.Component(self.board, model='background_image')
        with h.div:
            input_id = h.generate_id()
            submit_id = h.generate_id("image_position_submit")
            h << h.script(u'''YAHOO.util.Event.onDOMReady(function() {
                YAHOO.util.Event.on(%(input_id)s, 'change', function() { YAHOO.util.Dom.get(%(submit_id)s).click(); });
            });''' % {'input_id': ajax.py2js(input_id, h),
                      'submit_id': ajax.py2js(submit_id, h)})
            with h.form:
                h << h.label(_(u'Image position'), for_=input_id)
                with h.select(id_=input_id).action(self.background_position):
                    for value, name in BACKGROUND_POSITIONS:
                        h << h.option(_(name), value=value).selected(self.background_position())
                h << h.input(class_='hidden', id_=submit_id, type="submit").action(self.set_background_position)

    with h.div(class_='panel-section'):
        h << h.div(_(u'Board title color'), class_='panel-section-title')
        with h.div:
            with h.div:
                h << comp.render(h, model='title-color-edit')
                h << ' ' << _('or') << ' '
                h << h.a(_('Reset to default color')).action(self.reset_color)
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
    h << component.Component(overlay.Overlay(lambda r: comp.render(r, model='title-color'),
                                             lambda r: comp.render(r,
                                                                   model='title-color-overlay'),
                                             dynamic=False,
                                             title=_('Change color')))
    return h.root


@presentation.render_for(BoardBackground, model='title-color')
def render_board_background_title_color(self, h, comp, *args):
    style = 'background-color:%s' % (self.board.title_color or u'')
    h << h.span(class_='board-title-color', style=style)
    return h.root


@presentation.render_for(BoardBackground, model='title-color-overlay')
def render_board_background_title_color_overlay(self, h, comp, *args):
    """Color chooser contained in the overlay body"""
    v = var.Var(self.board.title_color)
    i = h.generate_id()
    h << h.div(id=i, class_='label-color-picker clearfix')
    with h.form:
        h << h.input(type='hidden', value=v(), id='%s-hex-value' % i).action(v)
        h << h.button(_('Save'), class_='btn btn-primary').action(
            ajax.Update(action=lambda v=v: self.set_color(v())))
        h << ' '
        h << h.button(_('Cancel'), class_='btn').action(lambda: None)
    h << h.script("YAHOO.kansha.app.addColorPicker(%s)" % ajax.py2js(i))
    return h.root

##### BoardsManager


@presentation.render_for(BoardsManager)
def render_userboards(self, h, comp, *args):
    template = var.Var(u'')
    h.head << h.head.title(self.app_title)

    h.head.css_url('css/themes/home.css?v=2c')
    h.head.css_url('css/themes/%s/home.css?v=2c' % self.theme)

    default_template_i18n = {
        'Empty board': _(u'Empty board'),
        'Basic Kanban': _(u'Basic Kanban')
    }

    with h.div(class_='new-board'):
        with h.form:
            h << h.SyncRenderer().button(_(u'Create'), type='submit', class_='btn btn-primary').action(lambda: self.create_board(template(), comp))
            h << (u' ', _(u'a new'), u' ')

            if len(self.templates) > 1:
                with h.select.action(template):
                    with h.optgroup(label=_(u'Shared templates')):
                        h << [h.option(default_template_i18n.get(tpl, tpl), value=id_) for
                              id_, tpl in self.templates['public']]
                    if self.templates['private']:
                        with h.optgroup(label=_(u'My templates')):
                            h << [h.option(_(tpl), value=id_) for
                                  id_, tpl in self.templates['private']]
            else:
                id_, tpl = self.templates.items()[0]
                template(id_)
                h << tpl

    if self.last_modified_boards:
        h << h.h1(_(u'Last modified boards'))
        with h.ul(class_='board-labels'):
            h << [b.on_answer(self.handle_event).render(h, 'item') for b in self.last_modified_boards]

    h << h.h1(_(u'My boards'))
    if self.my_boards:
        with h.ul(class_='board-labels'):
            h << [b.on_answer(self.handle_event).render(h, 'item') for b in self.my_boards]
    else:
        h << h.p(_(u'Create a board by choosing a template in the menu above, then click on the "Create" button.'))

    if self.guest_boards:
        h << h.h1(_(u'Guest boards'))
        with h.ul(class_='board-labels'):
            h << [b.on_answer(self.handle_event).render(h, 'item') for b in self.guest_boards]

    if self.shared_boards:
        h << h.h1(_(u'Shared boards'))
        with h.ul(class_='board-labels'):
            h << [b.on_answer(self.handle_event).render(h, 'item') for b in self.shared_boards]

    if len(self.archived_boards):
        h << h.h1(_('Archived boards'))

        with h.ul(class_='board-labels'):
            h << [b.on_answer(self.handle_event).render(h, 'archived_item')
                  for b in self.archived_boards]

        with h.form:
            h << h.SyncRenderer().button(
                _('Delete the archived board') if len(self.archived_boards) == 1 else _('Delete the archived boards'),
                class_='delete',
                onclick='return confirm(%s)' % ajax.py2js(
                    _('Deleted boards cannot be restored. Are you sure?')
                ).decode('UTF-8'),
                type='submit'
            ).action(self.purge_archived_boards)

    h << h.script('YAHOO.kansha.app.hideOverlay();'
                  'function reload_boards() { %s; }' % h.AsyncRenderer().a.action(ajax.Update(action=self.load_user_boards, render=0)).get('onclick'))

    return h.root
