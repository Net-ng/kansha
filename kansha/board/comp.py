# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import re
import json
import unicodedata
from cStringIO import StringIO
from functools import partial

import xlwt
from webob import exc
from nagare.database import session
from nagare.i18n import _, format_date
from nagare import component, log, security, var

from kansha import title
from kansha.card import fts_schema
from kansha.user import usermanager
from kansha.services import ActionLog
from kansha.column import comp as column
from kansha.user.comp import PendingUser
from kansha.toolbox import popin, overlay
from kansha.card_addons.label import Label
from kansha.authentication.database import forms
from kansha import events, exceptions, validator

from .boardconfig import BoardConfig
from .templates import SaveTemplateTask
from .models import DataBoard, DataBoardMember


# Board visibility
BOARD_PRIVATE = 0
BOARD_PUBLIC = 1

# Votes authorizations
VOTES_OFF = 0
VOTES_MEMBERS = 1
VOTES_PUBLIC = 2

# Comments authorizations
COMMENTS_OFF = 0
COMMENTS_MEMBERS = 1
COMMENTS_PUBLIC = 2


# WEIGHTING CARDS
WEIGHTING_OFF = 0
WEIGHTING_FREE = 1
WEIGHTING_LIST = 2


class Board(events.EventHandlerMixIn):

    """Board component"""

    max_shown_members = 4
    background_max_size = 3 * 1024  # in Bytes

    def __init__(self, id_, app_title, app_banner, theme, card_extensions, search_engine,
                 assets_manager_service, mail_sender_service, services_service,
                 load_children=True):
        """Initialization

        In:
          -- ``id_`` -- the id of the board in the database
          -- ``mail_sender_service`` -- Mail service, used to send mail
          -- ``on_board_delete`` -- function to call when the board is deleted
        """
        self.model = 'columns'
        self.app_title = app_title
        self.app_banner = app_banner
        self.theme = theme
        self.mail_sender = mail_sender_service
        self.id = id_
        self.assets_manager = assets_manager_service
        self.search_engine = search_engine
        self._services = services_service
        self.card_extensions = card_extensions

        self.action_log = ActionLog(self)

        self.version = self.data.version
        self.modal = component.Component(popin.Empty())
        self.card_matches = set()  # search results
        self.last_search = u''

        self.columns = []
        self.archive_column = None
        if load_children:
            self.load_children()

        # Member part
        self.overlay_add_members = component.Component(
            overlay.Overlay(lambda r: (r.i(class_='ico-btn icon-user'), r.span(_(u'+'), class_='count')),
                            lambda r: component.Component(self).render(r, model='add_member_overlay'),
                            dynamic=True, cls='board-labels-overlay'))
        self.new_member = component.Component(usermanager.NewMember(self.autocomplete_method))

        self.update_members()

        def many_user_render(h, number):
            return h.span(
                h.i(class_='ico-btn icon-user'),
                h.span(number, class_='count'),
                title=_("%s more...") % number)

        self.see_all_members = component.Component(overlay.Overlay(lambda r: many_user_render(r, len(self.all_members) - self.max_shown_members),
                                                                   lambda r: component.Component(self).render(r, model='members_list_overlay'),
                                                                   dynamic=False, cls='board-labels-overlay'))
        self.see_all_members_compact = component.Component(overlay.Overlay(lambda r: many_user_render(r, len(self.all_members)),
                                                                           lambda r: component.Component(self).render(r, model='members_list_overlay'),
                                                                           dynamic=False, cls='board-labels-overlay'))

        self.comp_members = component.Component(self)

        # Icons for the toolbar
        self.icons = {'add_list': component.Component(Icon('icon-plus', _('Add list'))),
                      'edit_desc': component.Component(Icon('icon-pencil', _('Edit board description'))),
                      'preferences': component.Component(Icon('icon-cog', _('Preferences'))),
                      'export': component.Component(Icon('icon-download3', _('Export board'))),
                      'save_template': component.Component(Icon('icon-floppy', _('Save as template'))),
                      'archive': component.Component(Icon('icon-trashcan', _('Archive board'))),
                      'leave': component.Component(Icon('icon-exit', _('Leave this board'))),
                      'history': component.Component(Icon('icon-history', _("Action log"))),
                      }

        # Title component
        self.title = component.Component(
            title.EditableTitle(self.get_title)).on_answer(self.set_title)

        self.must_reload_search = False

    @classmethod
    def get_id_by_uri(cls, uri):
        board = DataBoard.get_by_uri(uri)
        board_id = None
        if board is not None:
            board_id = board.id
        return board_id

    @classmethod
    def exists(cls, **kw):
        return DataBoard.exists(**kw)

    # Main menu actions
    def add_list(self):
        new_column_editor = column.NewColumnEditor(len(self.columns))
        answer = self.modal.call(popin.Modal(new_column_editor))
        if answer:
            index, title, nb_cards = answer
            self.create_column(index, title, nb_cards if nb_cards else None)

    def edit_description(self):
        description_editor = BoardDescription(self.get_description())
        answer = self.modal.call(popin.Modal(description_editor))
        if answer is not None:
            self.set_description(answer)

    def save_template(self, comp):
        save_template_editor = SaveTemplateTask(self.get_title(),
                                                self.get_description(),
                                                partial(self.save_as_template, comp))
        self.modal.call(popin.Modal(save_template_editor))

    def show_actionlog(self):
        self.modal.call(popin.Modal(self.action_log))

    def show_preferences(self):
        preferences = BoardConfig(self)
        self.modal.call(popin.Modal(preferences))

    def save_as_template(self, comp, title, description, shared):
        data = (title, description, shared)
        return self.emit_event(comp, events.NewTemplateRequested, data)

    def copy(self, owner, additional_data):
        """
        Create a new board that is a copy of self, without the archive.
        Children must be loaded.
        """
        new_data = self.data.copy(None)
        if self.data.background_image:
            new_data.background_image = self.assets_manager.copy(self.data.background_image)
        new_board = self._services(Board, new_data.id, self.app_title, self.app_banner, self.theme, self.card_extensions, self.search_engine, load_children=False)
        new_board.add_member(owner, 'manager')
        additional_data['author'] = owner

        additional_data['labels'] = []
        for lbl in self.labels:
            new_label = lbl.copy(new_board, additional_data)
            additional_data['labels'].append(new_label)
            new_board.labels.append(new_label)

        assert(self.columns or self.data.template)
        cols = [col() for col in self.columns if not col().is_archive]
        for column in cols:
            new_col = column.copy(new_board, additional_data)
            new_board.columns.append(component.Component(new_col))

        return new_board

    def on_event(self, comp, event):
        result = None
        if event.is_(events.ColumnDeleted):
            # actually delete the column
            result = self.delete_column(event.data)
        elif event.is_(events.CardArchived):
            result = self.archive_card(event.emitter)
        elif event.is_(events.SearchIndexUpdated):
            result = self.set_reload_search()
        elif event.is_(events.CardDisplayed):
            if self.must_reload_search:
                self.reload_search()
                result = 'reload_search'
            else:
                result = 'nop'

        return result

    def switch_view(self):
        self.model = 'calendar' if self.model == 'columns' else 'columns'

    def load_children(self):
        columns = []
        for c in self.data.columns:
            col = self._services(
                column.Column, c.id, self, self.card_extensions,
                self.action_log, self.search_engine, data=c)
            if col.is_archive:
                self.archive_column = col
            columns.append(component.Component(col))

        self.columns = columns

    def increase_version(self):
        refresh = False
        self.version += 1
        self.data.increase_version()
        if self.data.version - self.version != 0:
            self.refresh()  # when does that happen?
            self.version = self.data.version
            refresh = True
        return refresh

    def refresh(self):
        print "refresh!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        print "if you see this message, please contact RTE."
        self.load_children()

    @property
    def all_members(self):
        return self.managers + self.members + self.pending

    def update_members(self):
        """Update members section

        Recalculate members + managers + pending
        Recreate overlays
        """
        data = self.data
        members = [dbm.member for dbm in data.board_members]
        members = [member for member in set(members) - set(data.managers)]
        members.sort(key=lambda m: (m.fullname, m.email))
        self.members = [component.Component(BoardMember(usermanager.UserManager.get_app_user(member.username, data=member), self, 'member'))
                        for member in members]
        self.managers = [component.Component(BoardMember(usermanager.UserManager.get_app_user(member.username, data=member), self, 'manager' if len(data.managers) != 1 else 'last_manager'))
                         for member in data.managers]
        self.pending = [component.Component(BoardMember(PendingUser(token.token), self, 'pending'))
                        for token in data.pending]

    def set_title(self, title):
        """Set title

        In:
            - ``title`` -- new title
        """
        self.data.title = title

    def get_title(self):
        """Get title

        Return :
            - the board title
        """
        return self.data.title

    def mark_as_template(self, template=True):
        self.data.is_template = template

    def count_columns(self):
        """Return the number of columns
        """
        return len(self.columns)

    def create_column(self, index, title, nb_cards=None):
        """Create a new column in the board

        In:
            - ``index`` -- the position of the column as an integer
            - ``title`` -- the title of the new column
            - ``nb_cards`` -- the number of maximun cards on the colum
        """
        if index < 0:
            index = index + len(self.columns) + 1
        security.check_permissions('edit', self)
        if title == '':
            return False
        col = self.data.create_column(index, title, nb_cards)
        col_obj = self._services(
            column.Column, col.id, self,
            self.card_extensions, self.action_log, self.search_engine)
        self.columns.insert(
            index, component.Component(col_obj))
        self.increase_version()
        return col_obj

    def delete_column(self, col_comp):
        """Delete a board's column

        In:
            - ``id_`` -- the id of the column to delete
        """

        security.check_permissions('edit', self)
        self.columns.remove(col_comp)
        col_comp().delete()
        self.increase_version()
        return popin.Empty()

    def update_card_position(self, data):
        security.check_permissions('edit', self)
        data = json.loads(data)

        cols = {}
        for col in self.columns:
            cols[col().id] = (col(), col)

        orig, __ = cols[data['orig']]

        dest, dest_comp = cols[data['dest']]
        card_comp = orig.remove_card_by_id(data['card'])
        dest.insert_card_comp(dest_comp, data['index'], card_comp)
        card = card_comp()
        values = {'from': orig.get_title(),
                  'to': dest.get_title(),
                  'card': card.get_title()}
        self.action_log.for_card(card).add_history(
            security.get_user(),
            u'card_move', values)
        # reindex it in case it has been moved to the archive column
        scard = fts_schema.Card(**card.to_document())
        self.search_engine.update_document(scard)
        self.search_engine.commit()
        session.flush()

    def update_column_position(self, data):
        security.check_permissions('edit', self)
        data = json.loads(data)
        cols = []
        found = None
        for col in self.columns:
            if col().id == data['list']:
                found = col
            else:
                cols.append(col)
        cols.insert(data['index'], found)
        for i, col in enumerate(cols):
            col().change_index(i)
        self.columns = cols
        session.flush()

    @property
    def visibility(self):
        return self.data.visibility

    def is_public(self):
        return self.visibility == BOARD_PUBLIC

    def set_visibility(self, visibility):
        """Changes board visibility

        If new visibility is "Member" and comments/votes permissions
        are in "Public" changes them to "Members"

        In:
         - ``visibility`` -- an integer, new visibility (Private or Public)
        """
        if self.comments_allowed == COMMENTS_PUBLIC:
            # If comments are PUBLIC that means the board was PUBLIC and
            # go to PRIVATE. That's why we don't test the visibility
            # input variable
            self.allow_comments(COMMENTS_MEMBERS)
        if self.votes_allowed == VOTES_PUBLIC:
            self.allow_votes(VOTES_MEMBERS)
        self.data.visibility = visibility

    @property
    def archived(self):
        return self.data.archived

    @property
    def show_archive(self):
        return self.data.show_archive

    @show_archive.setter
    def show_archive(self, value):
        self.data.show_archive = value
        self.set_reload_search()

    def archive_card(self, card):
        """Archive card

        In:
            - ``card`` -- card to archive
        """
        self.archive_column.append_card(card)
        self.archive_column.refresh()

    @property
    def weighting_cards(self):
        return self.data.weighting_cards

    def activate_weighting(self, weighting_type):
        if weighting_type == WEIGHTING_FREE:
            self.data.weighting_cards = 1
        elif weighting_type == WEIGHTING_LIST:
            self.data.weighting_cards = 2

        # reinitialize cards weights
        for col in self.columns:
            col = col().data
            for card in col.cards:
                card.weight = ''
        for card in self.archive_column.cards:
            card.weight = ''

    @property
    def weights(self):
        return self.data.weights

    @weights.setter
    def weights(self, weights):
        self.data.weights = weights

    def deactivate_weighting(self):
        self.data.weighting_cards = 0
        self.data.weights = ''

    def delete_clicked(self, comp):
        return self.emit_event(comp, events.BoardDeleted)

    def delete(self):
        """Deletes the board.
           Children must be loaded.
        """
        assert(self.columns)  # at least, contains the archive
        for column in self.columns:
            column().delete(purge=True)
        self.data.delete_history()
        self.data.delete_members()
        session.refresh(self.data)
        self.data.delete()

        return True

    def archive(self, comp=None):
        """Archive the board
        """
        self.data.archived = True
        if comp:
            self.emit_event(comp, events.BoardArchived)
        return True

    def restore(self, comp=None):
        """Unarchive the board
        """
        self.data.archived = False
        if comp:
            self.emit_event(comp, events.BoardRestored)
        return True

    def leave(self, comp=None):
        """Children must be loaded."""
        # FIXME: all member management function should live in another component than Board.
        user = security.get_user()
        for member in self.members:
            m_user = member().user().data
            if (m_user.username, m_user.source) == (user.data.username, user.data.source):
                board_member = member()
                break
        else:
            board_member = None
        self.data.remove_member(board_member)
        if user.is_manager(self):
            self.data.remove_manager(board_member)
        if not self.columns:
            self.load_children()
        for column in self.columns:
            column().remove_board_member(user)
        if comp:
            self.emit_event(comp, events.BoardLeft)
        return True

    def export(self):
        sheet_name = fname = unicodedata.normalize('NFKD', self.data.title).encode('ascii', 'ignore')
        fname = re.sub('\W+', '_', fname.lower())
        sheet_name = re.sub('\W+', ' ', sheet_name)
        f = StringIO()
        wb = xlwt.Workbook()
        ws = wb.add_sheet(sheet_name[:31])
        sty = ''
        header_sty = xlwt.easyxf(sty + 'font: bold on; align: wrap on, vert centre, horiz center;')
        sty = xlwt.easyxf(sty)
        titles = [_(u'Column'), _(u'Title'), _(u'Description'), _(u'Due date')]

        if self.weighting_cards:
            titles.append(_(u'Weight'))
        titles.append(_(u'Comments'))

        for col, title in enumerate(titles):
            ws.write(0, col, title, style=header_sty)
        row = 1
        max_len = len(titles)
        for col in self.columns:
            col = col().data
            for card in col.cards:
                colnumber = 0
                ws.write(row, colnumber, _('Archived cards') if col.archive else col.title, sty)
                colnumber += 1
                ws.write(row, colnumber, card.title, sty)
                colnumber += 1
                ws.write(row, colnumber, card.description, sty)
                colnumber += 1
                ws.write(row, colnumber, format_date(card.due_date) if card.due_date else u'', sty)
                colnumber += 1
                if self.weighting_cards:
                    ws.write(row, colnumber, card.weight, sty)
                    colnumber += 1

                for colno, comment in enumerate(card.comments, colnumber):
                    ws.write(row, colno, comment.comment, sty)
                    max_len = max(max_len, 4 + colno)
                row += 1
        for col in xrange(len(titles)):
            ws.col(col).width = 0x3000
        ws.set_panes_frozen(True)
        ws.set_horz_split_pos(1)
        wb.save(f)
        f.seek(0)
        e = exc.HTTPOk()
        e.content_type = 'application/vnd.ms-excel'
        e.content_disposition = u'attachment;filename=%s.xls' % fname
        e.body = f.getvalue()
        raise e

    @property
    def labels(self):
        """Returns the labels associated with the board
        """
        return [self._services(Label, data) for data in self.data.labels]

    @property
    def data(self):
        """Return the board object from database
        """
        return DataBoard.get(self.id)

    def allow_comments(self, v):
        """Changes permission to add comments

        In:
            - ``v`` -- a integer (see security.py for authorized values)
        """
        self.data.comments_allowed = v

    def allow_votes(self, v):
        """Changes permission to vote

        In:
            - ``v`` -- a integer (see security.py for authorized values)
        """
        self.data.votes_allowed = v

    @property
    def comments_allowed(self):
        return self.data.comments_allowed

    @property
    def votes_allowed(self):
        return self.data.votes_allowed

    # Callbacks for BoardDescription component
    def get_description(self):
        return self.data.description

    def set_description(self, value):
        self.data.description = value


    ##################
    # Member methods
    ##################

    def last_manager(self, member):
        """Return True if member is the last manager of the board

        In:
         - ``member`` -- member to test
        Return:
         - True if member is the last manager of the board
        """
        return self.data.last_manager(member)

    def has_member(self, user):
        """Return True if user is member of the board

        In:
         - ``user`` -- user to test (User instance)
        Return:
         - True if user is member of the board
        """
        return self.data.has_member(user)

    def has_manager(self, user):
        """Return True if user is manager of the board

        In:
         - ``user`` -- user to test (User instance)
        Return:
         - True if user is manager of the board
        """
        return self.data.has_manager(user)

    def add_member(self, new_member, role='member'):
        """ Add new member to the board

        In:
         - ``new_member`` -- user to add (DataUser instance)
         - ``role`` -- role's member (manager or member)
        """
        self.data.add_member(new_member, role)

    def remove_pending(self, member):
        # remove from pending list
        self.pending = [p for p in self.pending if p() != member]

        # remove invitation
        self.remove_invitation(member.username)

    def remove_manager(self, manager):
        # remove from managers list
        self.managers = [p for p in self.managers if p() != manager]
        # remove manager from data part
        self.data.remove_manager(manager)

    def remove_member(self, member):
        # remove from members list
        self.members = [p for p in self.members if p() != member]
        # remove member from data part
        self.data.remove_member(member)

    def remove_board_member(self, member):
        """Remove member from board

        Remove member from board. If member is PendingUser then remove
        invitation.

        Children must be loaded for propagation to the cards.

        In:
            - ``member`` -- Board Member instance to remove
        """
        if self.last_manager(member):
            # Can't remove last manager
            raise exceptions.KanshaException(_("Can't remove last manager"))

        log.info('Removing member %s' % (member,))
        remove_method = {'pending': self.remove_pending,
                         'manager': self.remove_manager,
                         'member': self.remove_member}
        remove_method[member.role](member)

        # remove member from columns
        # FIXME: this function should live in a board extension that has its own data and
        # should not rely on a full component tree.
        if not self.columns:
            self.load_children()
        for c in self.columns:
            c().remove_board_member(member)

    def change_role(self, member, new_role):
        """Change member's role

        In:
            - ``member`` -- Board member instance
            - ``new_role`` -- new role
        """
        log.info('Changing role of %s to %s' % (member, new_role))
        if self.last_manager(member):
            raise exceptions.KanshaException(_("Can't remove last manager"))

        self.data.change_role(member, new_role)
        self.update_members()

    def remove_invitation(self, email):
        """ Remove invitation

        In:
         - ``email`` -- guest email to invalidate
        """
        for token in self.data.pending:
            if token.username == email:
                token.delete()
                session.flush()
                break

    def invite_members(self, emails, application_url):
        """Invite somebody to this board,

        Create token used in invitation email.
        Store email in pending list.

        Params:
            - ``emails`` -- list of emails
        """
        for email in set(emails):
            # If user already exists add it to the board directly or invite it otherwise
            invitation = forms.EmailInvitation(self.app_title, self.app_banner, self.theme, email, security.get_user().data, self.data, application_url)
            invitation.send_email(self.mail_sender)

    def resend_invitation(self, pending_member, application_url):
        """Resend an invitation,

        Resend invitation to the pending member

        In:
            - ``pending_member`` -- Send invitation to this user (PendingMember instance)
        """
        email = pending_member.username
        invitation = forms.EmailInvitation(self.app_title, self.app_banner, self.theme, email, security.get_user().data, self.data, application_url)
        invitation.send_email(self.mail_sender)
        # re-calculate pending
        self.pending = [component.Component(BoardMember(PendingUser(token.token), self, "pending"))
                        for token in set(self.data.pending)]

################

    def autocomplete_method(self, v):
        """ Method called by autocomplete component.

        This method is called when you search a user on the add member
        overlay int the field autocomplete

        In:
            - ``v`` -- first letters of the username
        Return:
            - list of user (User instance)
        """
        users = usermanager.UserManager.search(v)
        results = []
        for user in users:
            if user.is_validated() and user.email not in [m().email for m in self.all_members]:
                results.append(user)
        return results

    def get_last_activity(self):
        return self.action_log.get_last_activity()

    def get_friends(self, user):
        """Return user friends for the current board

        Returned users which are not board's member and have not pending invitation

        Return:
         - list of user's friends (User instance) wrapped on component
        """
        already_in = set([m().email for m in self.all_members])
        best_friends = user.best_friends(already_in, 5)
        self._best_friends = [component.Component(usermanager.UserManager.get_app_user(u.username), "friend") for u in best_friends]
        return self._best_friends

    @property
    def favorites(self):
        """Return favorites users of the board

        Favorites users are most used users in this board

        Return:
            - a dictionary {'username', 'nb used'}
        """
        return self.get_member_stats()

    def get_member_stats(self):
        """Return the most used users in this column.

        Ask most used users to columns

        Return:
            - a dictionary {'username', 'nb used'}
        """
        member_stats = {}
        for c in self.columns:
            column_member_stats = c().get_member_stats()
            for username in column_member_stats:
                member_stats[username] = member_stats.get(username, 0) + column_member_stats[username]
        return member_stats

    def get_available_users(self):
        """Return list of member

        Return:
            - list of members
        """
        return [dbm.member for dbm in self.data.board_members]

    def get_pending_users(self):
        return self.data.get_pending_users()

    def set_background_image(self, new_file):
        """Set the board's background image
        In:
            - ``new_file`` -- the background image (FieldStorage)
        Return:
            nothing
        """
        if new_file is not None:
            fileid = self.assets_manager.save(new_file.file.read(),
                                              metadata={'filename': new_file.filename,
                                                        'content-type': new_file.type})
            self.data.background_image = fileid
        else:
            self.data.background_image = None

    def set_background_position(self, position):
        self.data.background_position = position

    @property
    def background_image_url(self):
        img = self.data.background_image
        try:
            return self.assets_manager.get_image_url(img, include_filename=False) if img else None
        except IOError:
            log.warning('Missing background %r for board %r', img, self.id)
            return None

    @property
    def background_image_position(self):
        return self.data.background_position or 'center'

    @property
    def title_color(self):
        return self.data.title_color

    def set_title_color(self, value):
        self.data.title_color = value or u''

    def search(self, query):
        self.last_search = query
        if query:
            condition = fts_schema.Card.match(query) & (fts_schema.Card.board_id == self.id)
            # do not query archived cards if archive column is hidden
            if not self.show_archive:
                condition &= (fts_schema.Card.archived == False)
            self.card_matches = set(doc._id for (_, doc) in self.search_engine.search(condition))
            # make the difference between empty search and no results
            if not self.card_matches:
                self.card_matches.add(None)
        else:
            self.card_matches = set()

    @staticmethod
    def get_all_board_ids():
        return DataBoard.get_all_board_ids()

    @staticmethod
    def get_templates_for(user_username, user_source):
        return DataBoard.get_templates_for(user_username, user_source, BOARD_PUBLIC)

    def set_reload_search(self):
        self.must_reload_search = True

    def reload_search(self):
        self.must_reload_search = False
        return self.search(self.last_search)

################


class Icon(object):

    def __init__(self, icon, title=None):
        """Create icon object

        In:
          - ``icon`` -- icon class name (use icomoon custom font)
          - ``title`` -- icon title (and alt)
        """
        self.icon = icon
        self.title = title

################


class BoardDescription(object):

    """Description component
    """

    def __init__(self, description):
        """Initialization

        In:
            - ``description`` -- callable that returns the description.
        """
        self.description = var.Var(description)

    def commit(self, comp):
        description = self.description().strip()
        if description:
            description = validator.clean_text(description)
        comp.answer(description)

    def cancel(self, comp):
        comp.answer(None)


class BoardMember(object):

    def __init__(self, user, board, role):
        self.user = component.Component(user)
        self.role = role
        self.board = board

    @property
    def data(self):
        member = DataBoardMember.query
        member = member.filter_by(board=self.board.data)
        member = member.filter_by(member=self.get_user_data())
        return member.first()

    def delete(self):
        session.delete(self.data)
        session.flush()

    @property
    def username(self):
        return self.user().username

    @property
    def email(self):
        return self.user().email

    def dispatch(self, action, application_url):
        if action == 'remove':
            self.board.remove_board_member(self)
        elif action == 'toggle_role':
            self.board.change_role(self, 'manager' if self.role == 'member' else 'member')
        elif action == 'resend':
            self.board.resend_invitation(self, application_url)

    def get_user_data(self):
        return self.user().data
