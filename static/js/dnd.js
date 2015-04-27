//--
// Copyright (c) 2012, Net-ng.
// All rights reserved.
//
// This software is licensed under the BSD License, as described in
// the file LICENSE.txt, which you should have received as part of
// this distribution.
//--

(function () {
    'use strict';
    var Y = YAHOO.util,
        Dom = Y.Dom,
        Event = Y.Event,
        ECN = Dom.getElementsByClassName,
        NS = YAHOO.namespace('kansha'),
        DDM = YAHOO.util.DDM;

    /**
     * Helper log function
     */
    var log = function (args) {
        var s = '', i;
        for (i in args) {
            s = s + args[i] + ' ';
        }
        console.log(s);
    };
    /**
     * A DnD proxy that scrolls his container
     * Sources:
     *  - http://new.davglass.com/files/yui/dd15/
     *  - yui dragdrop.js source
     */
    var ScrollProxy = function (id, sGroup, config) {
        ScrollProxy.superclass.constructor.apply(this, arguments);
        // Can drag using A elements
        this.invalidHandleTypes.A = false;
        // Disable drag for textarea and input elements
        this.invalidHandleTypes.TEXTAREA = 'TEXTAREA';
        this.invalidHandleTypes.INPUT = 'INPUT';
        // Element used for scrolling
        this.scrollParent = Dom.get(config.scrollParent);
        // Attributes used to determine the drag orientation
        this.lastX = 0;
        this.goingRight = false;
        this.lastY = 0;
        this.goingDown = false;
        this.scrollInt = null;
    };
    YAHOO.extend(ScrollProxy, YAHOO.util.DDProxy, {
        /**
         * Auto-scroll the lists div if the dragged object has been moved
         * beyond the visible viewport boundary.
         * @method autoScroll
         * @param {int} x the drag element's x position
         * @param {int} y the drag element's y position
         * @param {int} h the height of the drag element
         * @param {int} w the width of the drag element
         */
        autoScroll: function (x, y, h, w) {

            // How many pixels to scroll per autoscroll op.  This helps to
            // reduce clunky scrolling. IE is more sensitive about this ...
            // it needs this value to be higher.
            var scrAmt = (document.all) ? 80 : 30;
            // How close to the edge the cursor must be before we scroll
            var thresh = 50;

            // Horizontal scrolling is done on the scrollParent element
            // (not the window)
            // Right marker coordinates
            var rightMarker = Dom.getRegion(this.scrollParent).right - thresh;
            // Left marker coordinates
            var leftMarker = Dom.getRegion(this.scrollParent).left + thresh;
            // Current scroll left
            var sl = this.scrollParent.scrollLeft;

            // Scroll left
            YAHOO.log('autoScroll: ' + sl + '/' + x + '/' + leftMarker);

            if (sl > 0 && x < leftMarker) {
                this.scrollParent.scrollLeft = sl - scrAmt;
            }
            // Scroll right
            if (x + w > rightMarker) {
                this.scrollParent.scrollLeft = sl + scrAmt;
            }

            // Vertical scrolling
            // For mobile, scroll the client window
            if (YAHOO.kansha.app.isMobile()) {
                // Current scroll top
                var st = this.DDM.getScrollTop();
                // Top marker coordinates
                var topMarker = st + thresh;
                // Bottom marker coordinates
                var bottomMarker = st + this.DDM.getClientHeight() - thresh;

                // Scroll top
                if (st > 0 && y < topMarker) {
                    window.scrollTo(this.scrollParent.scrollLeft, st - scrAmt);
                }
                // Scroll bottom
                if (y + h > bottomMarker) {
                    window.scrollTo(this.scrollParent.scrollLeft, st + scrAmt);
                }
            }
            DDM.refreshCache();
        },
        /**
         * Update drag orientation
         */
        onDrag: function (e) {
            var c = Event.getXY(e);
            this.goingRight = (c[0] >= this.lastX);
            this.goingDown = (c[1] >= this.lastY);
            this.lastX = c[0];
            this.lastY = c[1];
        }
    });

    NS.dnd = {
        listMarker: undefined,
        cardMarker: undefined,
        init: function () {
            var target = new YAHOO.util.DDTarget(Dom.get('list-target'), 'list'),
                listBody;
            NS.dnd.listMarker = document.createElement('div');
            Dom.addClass(NS.dnd.listMarker, 'list-marker span3');

            NS.dnd.cardMarker = document.createElement('div');
            Dom.addClass(NS.dnd.cardMarker, 'card-marker');

            listBody = ECN('list-body', 'div', list_id);
            alert(listBody);
            target = YAHOO.util.DDTarget(listBody);
        },
        initConstraints: function (drag) {
            //Get Region wrapper
            var region = Dom.getRegion('viewport-wrapper');
            //Clear old constraints
            drag.clearConstraints();

            //Get the element we are working on
            var el = drag.getEl();

            //Get the xy position of it
            var xy = Dom.getXY(el);

            //Get the height
            var height = parseInt(Dom.getStyle(el, 'height'), 10);

            //Set top to y minus top
            var top = xy[1] - region.top;

            //Set bottom to bottom minus y minus height
            var bottom = region.bottom - xy[1] - height - 20;

            //Set the constraints based on the above calculations
            drag.setYConstraint(top, bottom);

            //resetConstraints must be called if you manually
            //reposition a dd element.
            drag.resetConstraints();
        },
        /**
         * Initialize DnD List
         */
        initList: function (list_id) {
            var drag = new ScrollProxy(list_id, 'list', {
                dragElId: 'dnd-frame',
                scrollParent: 'lists'
            });
            var handle = ECN('list-header', 'div', list_id).pop();
            drag.setHandleElId(Dom.getAttribute(handle, 'id'));

            drag.b4StartDrag = function (x, y) {
                this.showFrame(x, y);
                if (YAHOO.kansha.app.isDesktop()) {
                    this.clearConstraints();
                    this.setYConstraint(0, 0);
                } else {
                    this.clearConstraints();
                    this.setXConstraint(0, 0);
                }
                this.resetConstraints();
                YAHOO.kansha.app.hideOverlay();
            };

            drag.startDrag = function (x, y) {
                var src = this.getEl(),
                    dragEl = this.getDragEl(),
                    region = Dom.getRegion(src);
                Dom.batch(Selector.query('.list-header .list-actions', src), function (elem) {
                    YAHOO.kansha.app.show(elem, false);
                });
                if (YAHOO.kansha.app.isDesktop()) {
                    Dom.setAttribute(dragEl, 'class', 'list list-proxy');
                    Dom.setStyle(dragEl, 'height', dragEl.clientHeight - 4 + 'px');
                    Dom.setStyle(dragEl, 'width', dragEl.clientWidth - 4 + 'px');
                    Dom.setStyle(NS.dnd.listMarker, 'height', region.height - 2 + 'px');
                    Dom.setStyle(NS.dnd.listMarker, 'width', region.width + -2 + 'px');
                } else {
                    Dom.setAttribute(dragEl, 'class', 'list reduced');
                    Dom.setStyle(dragEl, 'height', 'auto');
                    Dom.setStyle(dragEl, 'width', '100%');
                    //define list marker style
                    Dom.setStyle(NS.dnd.listMarker, 'height', '30px');
                    Dom.setStyle(NS.dnd.listMarker, 'width', '99%');
                    //reduce all other column
                    Dom.setAttribute(ECN('list'), 'class', 'span-auto list reduced');
                }
                dragEl.innerHTML = src.innerHTML;
                src.parentNode.replaceChild(NS.dnd.listMarker, src);
            };

            drag.onDragEnter = function (e, id) {
                var func = null;
                if (YAHOO.kansha.app.isDesktop()) {// Column mode
                    func = (this.goingRight ? Dom.insertAfter : Dom.insertBefore);
                } else {// Vertical mode
                    func = (this.goingDown ? Dom.insertAfter : Dom.insertBefore);
                }
                if (func) {
                    func(NS.dnd.listMarker, id);
                    DDM.refreshCache();
                    // Important !
                }
            };

            drag.endDrag = function (e, id) {
                var clone = Dom.get(list_id);
                if (clone) {
                    clone.parentNode.removeChild(clone);
                }
                var dragEl = this.getDragEl();
                Dom.setAttribute(dragEl, 'class', '');
                NS.dnd.listMarker.parentNode.replaceChild(this.getEl(), NS.dnd.listMarker);
                Dom.batch(Dom.getChildren(dragEl), function (c) {
                    dragEl.removeChild(c);
                });
                if (!YAHOO.kansha.app.isDesktop()) {
                    Dom.setAttribute(ECN('list'), 'class', 'span-auto list');
                }

                Dom.setXY(dragEl, [0, 0]);
                var lists = Selector.query('.list');
                var index = 0;
                for (index = 0; index < lists.length; index++) {
                    if (Dom.getAttribute(lists[index], 'id') === list_id) {
                        break;
                    }
                }
                _send_column_position({'list': list_id, 'index': index});
                // Reset drag frame position
            };
        },
        initTargetCard: function (targetId) {
            var card = new YAHOO.util.DDTarget(targetId, 'card');
        },
        initCard: function (card) {
            var drag = new ScrollProxy(card, 'card', {
                dragElId: 'dnd-frame',
                scrollParent: 'lists'
            });

            drag.b4StartDrag = function (x, y) {
                this.showFrame(x, y);
                if (!YAHOO.kansha.app.isDesktop()) {
                    this.clearConstraints();
                    this.setXConstraint(0, 0);
                } else {
                    NS.dnd.initConstraints(this);
                }
                this.container = Dom.getAncestorByClassName(this.getEl(), 'list-body');
                this.origin = Dom.getAncestorByClassName(this.getEl(), 'list');
                YAHOO.kansha.app.hideOverlay();
            };

            drag.startDrag = function (x, y) {
                var src = this.getEl(),
                    dragEl = this.getDragEl(),
                    region = Dom.getRegion(src);
                Dom.getElementsByClassName('card', 'div', src, function (elem) {
                    YAHOO.kansha.app.highlight(elem, 'badges', true);
                    YAHOO.kansha.app.highlight(elem, 'members', true);
                });
                dragEl.innerHTML = src.innerHTML;
                Dom.addClass(dragEl, 'card-dragging');
                if (YAHOO.kansha.app.isDesktop()) {
                    Dom.setStyle(NS.dnd.cardMarker, 'height', region.height + 'px');
                } else {
                    Dom.setStyle(NS.dnd.cardMarker, 'height', '30px');
                }
                src.parentNode.replaceChild(NS.dnd.cardMarker, src);
            };

            drag.endDrag = function (e, id) {
                var el = this.getEl(),
                    dragEl = this.getDragEl(),
                    region = Dom.getRegion(NS.dnd.cardMarker);
                var self = this;

                var origCard = Selector.query('.card', this.getEl(), true);
                var clone = Dom.get(Dom.getAttribute(origCard, 'id'));

                Dom.setStyle(dragEl, 'visibility', '');

                var a = new YAHOO.util.Motion(dragEl, {
                    points: {
                        to: [region.x, region.y]
                    }
                }, 0.15);

                a.onComplete.subscribe(function () {
                    NS.dnd.cardMarker.parentNode.replaceChild(el, NS.dnd.cardMarker);

                    Dom.batch(Dom.getChildren(dragEl), function (c) {
                        dragEl.removeChild(c);
                    });
                    Dom.setStyle(this.getEl(), 'visibility', 'hidden');

                    Dom.setXY(dragEl, [0, 0]);
                    // Reset drag frame position
                    var cardId = Dom.getAttribute(Selector.query('.card', card, true), 'id');
                    var dest = Dom.getAncestorByClassName(card, 'list');
                    var cards = Selector.query('.card', dest);
                    var index = 0;
                    for (index = 0; index < cards.length; index++) {
                        if (Dom.getAttribute(cards[index], 'id') === cardId) {
                            break;
                        }
                    }

                    if (clone) {
                        clone.parentNode.removeChild(clone);
                    }

                    var data = {dest: Dom.getAttribute(dest, 'id'),
                                orig: Dom.getAttribute(self.origin, 'id'),
                                card: cardId, index: index};
                    YAHOO.kansha.app.countCards(dest);
                    YAHOO.kansha.app.countCards(self.origin);
                    _send_card_position(data);
                });

                if (this.scrollInt) {
                    clearInterval(this.scrollInt);
                }

                a.animate();

            };
            drag.onDrag = function (e) {
                // copy onDrag basic instruction, is it possible to call the super method ?
                var c = Event.getXY(e);
                this.goingRight = (c[0] >= this.lastX);
                this.goingDown = (c[1] >= this.lastY);
                this.lastX = c[0];
                this.lastY = c[1];

                var y = Event.getPageY(e),
                    scrollTop = false,
                    xy = Dom.getXY(this.container),
                    topMarker = xy[1] + 50,
                    bottomMarker = xy[1] + this.container.clientHeight - 50;

                if (this.goingDown) {
                    if (y > bottomMarker) {
                        scrollTop = this.container.scrollTop + 20;
                    }
                } else {
                    if (y < topMarker) {
                        scrollTop = this.container.scrollTop - 20;
                    }
                }
                this.scrollTo(scrollTop);
            };
            drag.onDragEnter = function (e, id) {
                var destEl = Dom.get(id);
                var srcEl = this.getEl();
                var list = Dom.getAncestorByClassName(id, 'list');
                var limit = parseInt(localStorage[list.id],10);
                var cards = ECN('card', null, list);
                if (destEl.className == 'list-body') {
                    // insert cardMarker at the end
                    if (cards.length < limit || limit === 0) {
                        destEl.appendChild(NS.dnd.cardMarker);
                        DDM.refreshCache();
                        this.container = Dom.get(id);
                    }
                } else {
                    this.container = Dom.getAncestorByClassName(id, 'list-body');
                }
            };
            drag.onDragOver = function (e, id) {
                var destEl = Dom.get(id);
                var srcEl = this.getEl();
                if (destEl.className != 'list-body') {
                    var list = Dom.getAncestorByClassName(id, 'list');
                    var limit = parseInt(localStorage[list.id],10);
                    var cards = ECN('card', null, list);

                    if (cards.length < limit || limit === 0) {
                        if (this.goingDown) {
                            Dom.insertAfter(NS.dnd.cardMarker, id);
                            // insert above
                        } else {
                            Dom.insertBefore(NS.dnd.cardMarker, id);
                            // insert below
                        }
                    }
                    DDM.refreshCache();
                }
            };
            drag.scrollTo = function (scrollTop) {
                // first step
                // TODO: Use clearInterval method for continue scrolling
                // when cursor doesn't move
                this.currentScrollTop = scrollTop;
                if (this.scrollInt) {
                    clearInterval(this.scrollInt);
                }
                if (scrollTop) {
                    var self = this;
                    this.scrollInt = setInterval(function () {
                        if ((self.currentScrollTop < 0) ||
                                (self.currentScrollTop > self.container.scrollHeight)) {
                            clearInterval(self.scrollInt);
                        }
                        self.container.scrollTop = self.currentScrollTop;
                        DDM.refreshCache();
                        if (self.goingDown) {
                            self.currentScrollTop += 20;
                        } else {
                            self.currentScrollTop -= 20;
                        }
                    }, 10);
                }
            };


        }
    };
}());

YAHOO.util.Event.onDOMReady(YAHOO.kansha.dnd.init);
