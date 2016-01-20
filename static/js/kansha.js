//--
// Copyright (c) 2012, Net-ng.
// All rights reserved.
//
// This software is licensed under the BSD License, as described in
// the file LICENSE.txt, which you should have received as part of
// this distribution.
//--

(function () {
    var Y = YAHOO.util,
        Anim = Y.Anim,
        Dom = Y.Dom,
        Event = Y.Event,
        Selector = Y.Selector,
        ECN = Dom.getElementsByClassName,
        ACN = Dom.getAncestorByClassName,
        NS = YAHOO.namespace('kansha');
    // methods to refresh cards
    NS.reload_cards = {};

    NS.app = {
        panel: undefined,
        overlay: undefined,
        resize: null,
        listsHeight: null,
        closePopinFunction: null,
        timeZoneOffset: new Date().getTimezoneOffset(),
        /**
         * Avoid multiple calls when we are interested only in the last event.
         * Eg. wait for the final resize event.
         */
        waitForFinalEvent: (function () {
            var timers = {};
            return function (callback, ms, uniqueId) {
                if (!uniqueId) {
                    uniqueId = "Don't call this twice without a uniqueId";
                }
                if (timers[uniqueId]) {
                    clearTimeout(timers[uniqueId]);
                }
                timers[uniqueId] = setTimeout(callback, ms);
            };
        }()),

        /**
         * App initialization :
         *    - register events
         */
        init: function () {
            Event.addListener(window, "click", NS.app.onClick);
            Event.addListener(window, "dblClick", NS.app.onDblClick);
            var link = document.URL.split('#');
            if (link.length > 1) {
                link = Dom.get(link[1].substring(3));
                if (link && link.firstChild) {
                    link.firstChild.click();
                }
            }
        },

        /**
         * List initialization :
         *  - set max-height
         *  - show/hide of menu icon
         */
        initList: function (col) {
            col = Dom.get(col);
            var showHide = function (root, show) {
                var node = ECN('list-actions', 'div', root).pop();
                NS.app.show(node, show);
            };

            Event.on(ECN('list-header', 'div', col), 'mouseover', function (ev) {
                Event.stopEvent(ev);
                var show = this.getElementsByTagName('form').length === 0;
                showHide(this, show);
            });

            Event.on(ECN('list-header', 'div', col), 'mouseout', function (ev) {
                Event.stopEvent(ev);
                showHide(this, false);
            });
        },

        /**
         * Basic show/hide function
         */
        show: function (el, show) {
            var node = Dom.get(el),
                func = show ? Dom.removeClass : Dom.addClass;
            func(node, 'hidden');
        },

        /**
         * Hightlight cards
         * Parameter: list of card ids
         */
        highlight_cards: function (card_ids) {
            var root = Dom.get('lists'),
                cards = ECN('card', 'div', root),
                search_input = Dom.get('search');
            Dom.removeClass(cards, 'highlight');
            if (card_ids.length > 0) {
                Dom.addClass(cards, 'hidden');
                Dom.replaceClass(card_ids, 'hidden', 'highlight');
                if (card_ids[0] === null) {
                    Dom.addClass(search_input, 'nomatches');
                } else {
                    Dom.addClass(search_input, 'highlight');
                }
            } else {
                Dom.removeClass(cards, 'hidden');
                Dom.removeClass(search_input, 'highlight');
                Dom.removeClass(search_input, 'nomatches');
            }
        },

        /**
         * Urlify HTML node content
         */
        urlify: function (root) {
            root.linkify();
            root.find('a').click(function (e) {
                e.stopPropagation();
            });
        },

        /**
         * Check if we are running on a desktop screen
         */
        isDesktop: function () {
            return Dom.getViewportWidth() >= 768;
        },

        /**
         * check if we are running on a mobile device such as smartphone
         */
        isMobile: function () {
            return !NS.app.isDesktop();
        },

        /**
         * Handle window resize
         */
        columnsResize: function () {
            // In desktop mode calculate size in percent for the columns
            var newList = Selector.query('#lists .new', null, true);
            var list;
            if (newList) {
                list = newList.firstChild;
                Dom.get('lists').replaceChild(list, newList);
            }
            var lists = ECN('list', 'div', 'lists');
            Dom.setStyle(lists, 'width', Math.round(92 / lists.length) + '%');
            if (newList) {
                lists = Dom.get('lists');
                lists.scrollLeft = list.offsetLeft - lists.offsetLeft;
                list.scrollIntoView();
            }
        },

        /**
         * Close all open overlays and popin
         */
        onClick: function (ev) {
            var target = Event.getTarget(ev),
                inOverlay = ACN(target, 'overlay') || Dom.hasClass(target, 'overlay'),
                inPanel = ACN(target, 'yui-panel') || Dom.hasClass(target, 'yui-panel'),
                InCkeditor = ACN(target, 'cke') || ACN(target, 'cke_dialog') || Dom.hasClass(target, 'cke') || Dom.hasClass(target, 'cke_dialog');
            /* do nothing if modal active */
            if (NS.app.modal) {
                return;
            }
            if (NS.app.overlay && !inOverlay) {
                NS.app.hideOverlay();
            }
            if (NS.app.popin && !inPanel && !inOverlay && !InCkeditor) {
                NS.app.closePopin();
            }
        },

        /**
         * Show the add list overlay
         * FIXME: ATM can't catch the double click event...
         */
        onDblClick: function (ev) {
            // TODO: show add list overlay
        },

        hideOverlay: function () {
            if (NS.app.overlay) {
                NS.app.overlay.hide();
                NS.app.overlay = undefined;
                return true;
            }
            return false;
        },

        onHideOverlay: function(callback) {
            NS.app.overlay.beforeHideEvent.subscribe(callback);
        },

        closeOverlay: function () {
            if (NS.app.hideOverlay()) {
                NS.app.overlay.destroy();
                NS.app.overlay = undefined;
                return true;
            }
            return false;
        },

        stopEvent: function () {
            var ev = Event.getEvent();
            Event.stopEvent(ev);
        },

        showOverlay: function (overlay_id, link_id, centered) {
            var ev = Event.getEvent();
            Event.stopEvent(ev);
            NS.app.hideOverlay();
            var link = Dom.get(link_id);
            var child = Dom.getFirstChild(link);
            var anchor = child ? child : link;
            var x = -10,
                y = 5;
            x += parseInt(Dom.getStyle(anchor, 'paddingLeft'), 10);
            NS.app.overlay = new YAHOO.widget.Overlay(overlay_id,
                {context: [anchor, 'tl', 'bl', ["beforeShow", "windowResize"], [x, y]],
                    zIndex: 1500,
                    visible: true,
                    constraintoviewport: true});
            NS.app.overlay.render(document.body);
            if (centered){
            	NS.app.overlay.center();
            }
            NS.app.overlay.show();
        },

        showPopin: function (id, closeFunction) {
            if (NS.app.isMobile()) {
                NS.app.show('application', false);
            }
            // Only one popin at a time
            // If we replace, don't fire previous closePopinFunction
            // (the callback must be lost anyway)
            if (NS.app.popin) {
                NS.app.closePopinFunction = null;
                NS.app.closePopin();
            }
            // Create the panel
            NS.app.popin = new YAHOO.widget.Panel(id, {
                modal: false,
                close: false,
                draggable: false,
                zIndex: 1000,
                underlay: 'none',
                constraintoviewport: true,
                monitorresize: false,
                // Add listener on the Esc key
                keylisteners: new YAHOO.util.KeyListener(document, {keys: 27}, NS.app.closePopin, 'keyup')
            });
            NS.app.popin.cfg.setProperty("x", 0);
            // Register the close function
            NS.app.closePopinFunction = closeFunction;
            // Render the panel
            NS.app.popin.render(document.body);
            YAHOO.util.Dom.setStyle('mask', 'display', 'block');
        },

        closePopin: function () {
            if (NS.app.popin) {
                // Launch the previously registered close function
                if (NS.app.closePopinFunction) {
                    NS.app.closePopinFunction();
                    NS.app.closePopinFunction = null;
                }
                // Destroy the panel
                NS.app.popin.destroy();
                NS.app.popin = null;
                // Remove the mask
                YAHOO.util.Dom.setStyle('mask', 'display', 'none');
            }
            if (NS.app.isMobile()) {
                NS.app.show('application', true);
            }
        },


        showModal: function (id) {
            if (NS.app.isMobile()) {
                NS.app.show('application', false);
            }
            // Create the panel
            NS.app.modal = new YAHOO.widget.Panel(id, {
                modal: true,
                close: false,
                draggable: false,
                zIndex: 2000,
                underlay: 'none',
                constraintoviewport: true,
                monitorresize: false
            });
            // No top/left offset
            NS.app.modal.cfg.setProperty("x", 0);
            // Render the panel
            NS.app.modal.render(document.body);
            YAHOO.util.Dom.setStyle(id, 'display', 'block');
            YAHOO.util.Dom.setStyle('mask', 'display', 'block');
        },

        closeModal: function () {
            if (NS.app.modal) {
                // Destroy the panel
                NS.app.modal.destroy();
                NS.app.modal = null;
                // Remove the mask if not already used
                if (!NS.app.popin) {
                    YAHOO.util.Dom.setStyle('mask', 'display', 'none');
                }
            }
            if (NS.app.isMobile()) {
                NS.app.show('application', true);
            }
        },

        deleteCard: function (deleteFunction, card_id, column_id) {
            //Close popin
            if (NS.app.popin) {
                deleteFunction();
                NS.app.popin.destroy();
                NS.app.popin = null;
                // Remove the mask
                YAHOO.util.Dom.setStyle('mask', 'display', 'none');
            }
            if (NS.app.isMobile()) {
                NS.app.show('application', true);
            }
            //Remove card from column
            var el = Dom.get(card_id),
                dndCard = el.parentNode.parentNode,
                parent = dndCard.parentNode;
            parent.removeChild(dndCard);
            NS.app.countCards(column_id);
            increase_version();
        },

        archiveCard: function (deleteFunction) {
            //Close popin
            if (NS.app.popin) {
                deleteFunction();
                NS.app.popin.destroy();
                NS.app.popin = null;
                // Remove the mask
                YAHOO.util.Dom.setStyle('mask', 'display', 'none');
            }
            if (NS.app.isMobile()) {
                NS.app.show('application', true);
            }

            increase_version();
        },

        /**
         * Select the content of a form element
         */
        selectElement: function (id) {
            YAHOO.util.Event.onDOMReady(function () {
                Dom.get(id).select();
            });
        },

        /**
         * Remove a list from the board
         */
        deleteList: function (list_id) {
            var el = Dom.get(list_id),
                parent = el.parentNode;
            NS.app.closeOverlay();
            parent.removeChild(el);
            NS.app.columnsResize();
        },

        /**
         * Ctrl+Enter handler for form fields
         */
        addCtrlEnterHandler: function (field, button) {
            Event.onDOMReady(function () {
                var listener = new YAHOO.util.KeyListener(field, {ctrl: true, keys: 13},
                    {fn: function () {
                        Dom.get(button).click();
                    }});
                listener.enable();
            });
        },

        /**
         * Autoheight
         */
        autoHeight: function (textarea) {
            var zone = Dom.get(textarea);
            var height = zone.scrollHeight;
            Dom.setStyle(zone, 'height', height + 'px');

            textarea.interval = setInterval(function () {
                zone = Dom.get(textarea);
                if (zone === null) {
                    clearInterval(textarea.interval);
                    return;
                }
                if (zone.clientHeight !== zone.scrollHeight) {
                    height = zone.scrollHeight;
                    Dom.setStyle(zone, 'height', height + 'px');
                }
            }, 100);
        },

        /**
         * Color picker
         */
        addColorPicker: function (id) {
            var hexValue = Dom.get(id + '-hex-value').value.replace('#', '');
            var colorPicker = new YAHOO.widget.ColorPicker(id, {
                showhsvcontrols: false,
                showrgbcontrols: false,
                showhexcontrols: false,
                showwebsafe: false,
                showhexsummary: false,
                rgb: YAHOO.util.Color.hex2rgb(hexValue),
                images: {
                    PICKER_THUMB: '/static/nagare/yui/build/colorpicker/assets/picker_thumb.png',
                    HUE_THUMB: '/static/nagare/yui/build/colorpicker/assets/hue_thumb.png'
                }
            });
            colorPicker.on('rgbChange', function (o) {
                var hex = YAHOO.util.Color.rgb2hex(o.newValue);
                Dom.get(id + '-hex-value').value = '#' + hex;
            });
        },

        /**
         * UTC to local time conversion
         */
        utcToLocal: function (id, utcSeconds, atTranslation, onTranslation) {
            var parent = YAHOO.util.Dom.get(id);
            if (!parent) {
                return;
            }
            var d = new Date(utcSeconds * 1000);
            var dToTest = new Date(utcSeconds * 1000);
            dToTest.setHours(0, 0, 0, 0);
            var dNow = new Date();
            dNow.setHours(0, 0, 0, 0);

            var toDisplay = onTranslation + ' ' + d.toLocaleDateString() + ' ' + atTranslation + ' ' + d.toLocaleTimeString();
            if (dToTest.getTime() === dNow.getTime()) {
                toDisplay = atTranslation + ' ' + d.toLocaleTimeString();
            }
            parent.innerHTML = toDisplay;
        },

        /**
         * Image cropper
         */
        initCrop: function (id, form_id, width, height) {
            var region = Dom.getRegion(id);
            var elmHeight = region.bottom - region.top;
            var elmWidth = region.right - region.left;
            if (elmWidth && elmHeight) {
                if (elmHeight < height) {
                    width = width * elmHeight / height;
                    height = elmHeight;
                }
                if (elmWidth < width) {
                    height = height * elmWidth / width;
                    width = elmWidth;
                }
            }

            var crop = new YAHOO.widget.ImageCropper(id, {initialXY: [0, 0], ratio: true, initWidth: width, initHeight: height, status: false});
            var updateCoords = function () {
                var region = crop.getCropCoords();
                Dom.get(form_id + '_crop_top').value = region.top;
                Dom.get(form_id + '_crop_left').value = region.left;
                Dom.get(form_id + '_crop_width').value = region.width;
                Dom.get(form_id + '_crop_height').value = region.height;
            };
            crop.on('dragEvent', updateCoords);
            crop.on('resizeEvent', updateCoords);
            updateCoords();
        },

        syncError: function (status, details) {
            var onClick = function () {
                Dom.get('resync-action').click();
            };
            Dom.setStyle('mask', 'z-index', '1750');
            Dom.setStyle('mask', 'display', 'block');
            Dom.setStyle('resync', 'display', 'block');
            Event.removeListener('mask', 'click');
            Event.addListener('mask', 'click', onClick);
            NS.app.showPopin('resync', onClick);
            NS.app.popin.cfg.setProperty('zIndex', 2000);
        },

        checkFileSize: function (input, maxSize) {
            if (input.files) {
                var i, file;
                for (i = 0; i < input.files.length; i++) {
                    file = input.files[i];
                    if (file.size / 1024 > maxSize) {
                        return false;
                    }
                }
            }
            return true;
        },

        countCards: function (column) {
            column = Dom.get(column);
            var counter = Dom.get(column.id + '_counter');
            if (counter) {
                var limit = parseInt(localStorage[column.id]);
                var header = Dom.get(column.id + '_header');
                var footer = Dom.get(column.id + '_footer');
                var cards = ECN('card', null, column);
                var numCards = cards.length;
                var textCount = limit > 0 ? numCards + '/' + limit : numCards;
                var counter = Dom.get(column.id + '_counter');
                var content = counter.childNodes[0];
                content.innerHTML = textCount;
                if (limit > 0 && numCards >= limit) {
                    Dom.addClass(counter, 'limitReached');
                    Dom.addClass(footer, 'hidden');
                    Dom.removeClass(counter, 'hidden');
                } else if (limit === 0) {
                    Dom.addClass(counter, 'hidden');
                } else {
                    Dom.removeClass(counter, 'limitReached');
                    Dom.removeClass(footer, 'hidden');
                }
            }
        },

        refreshCardsCounters: function () {
            Dom.batch(Selector.query('#lists .list'), this.countCards);
        },

        saveLimit: function (column, limit) {
            localStorage[Dom.get(column).id] = limit;
        },

        hideCardsLimitEdit: function (column) {
            column = Dom.get(column);
            var counter = Dom.get(column.id + '_counter');
            var option = Dom.get(column.id + '_counter_option');
            if (counter) {
                Dom.addClass(counter, 'hidden');
            }
        },

        showCardsLimitEdit: function (column) {
            column = Dom.get(column);
            var counter = Dom.get(column.id + '_counter');
            var option = Dom.get(column.id + '_counter_option');
            var limit = parseInt(localStorage[column.id], 10);
            if (counter && limit > 0) {
                Dom.removeClass(counter, 'hidden');
            }
            NS.app.showTitleForm(column.id);
        },

        setTitleColor: function (color) {
            Dom.setStyle(Selector.query('.board-title a'), 'color', color || '');
        },

        setBoardBackgroundImage: function (imageUrl, position) {
            var boardNode = Selector.query('#application .board', null, true);
            Dom.setStyle(boardNode, 'background-image', 'url(' + imageUrl + ')')
            Dom.setAttribute(boardNode, 'className', 'board ' + position);
        },

        create_board_calendar: function (calendar, displayWeekNumbers) {
            calendar.fullCalendar(
                {
                    aspectRatio: 2,
                    eventClick: function (calEvent, jsEvent, view) {
                        calEvent.clicked_cb();
                    },
                    eventDrop: function(calEvent, delta, revertFunc) {
                        calEvent.dropped_cb(calEvent.start.format());
                    },
                    weekNumbers: displayWeekNumbers,
                    weekNumberCalculation: "ISO",
                    firstDay: 1 // ISO week
                });
        },

        add_event: function (calendar, event, clicked_cb, dropped_cb) {
            var myEvent = event;
            myEvent.clicked_cb = clicked_cb;
            myEvent.dropped_cb = dropped_cb;
            calendar.fullCalendar('renderEvent', myEvent, true);
        },

        init_ckeditor: function(id, language) {
            var editor,
                element = Dom.get(id);
            editor = CKEDITOR.replace(id, {
                title: '',
                contentsCss: ['/static/kansha/css/themes/fonts.css',
                              '/static/kansha/css/ckeditor.css'],
                language: language,
                skin: 'bootstrapck',
                enterMode: CKEDITOR.ENTER_BR,
                shiftEnterMode: CKEDITOR.ENTER_BR,
                resize_enabled: false,
                forcePasteAsPlainText: true,
                removePlugins: 'stylescombo,magicline,elementspath,',
                toolbarGroups: [{"name": "basicstyles", "groups": ["basicstyles"]},
                    {"name": "links", "groups": ["links"]},
                    {"name": "paragraph", "groups": ["list"]}],
                removeButtons: 'Strike,Subscript,Superscript,Anchor,Styles,Specialchar'
            });
            editor.on('change', function(ev){
                 element.innerHTML = editor.getData();
            });
            editor.on('instanceReady', function() {
                editor.container.addClass('kansha-cke');
                editor.focus();
            });
        }

    };
}());

YAHOO.util.Event.onDOMReady(YAHOO.kansha.app.init);
