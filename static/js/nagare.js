//--
// Copyright (c) 2012, Net-ng.
// All rights reserved.
//
// This software is licensed under the BSD License, as described in
// the file LICENSE.txt, which you should have received as part of
// this distribution.
//--

var requestsByAction = {};
var requestsById = {};

function hasRequest(action) {
    return !YAHOO.lang.isUndefined(requestsByAction[action]);
}

function addRequest(id, action) {
    requestsByAction[action] = id;
    requestsById[id] = action;
}

function removeRequest(id) {
    var action = requestsById[id];
    delete requestsById[id];
    delete requestsByAction[action];
}

// Callbacks
nagare_callbacks = {
    failure: function (o) {
        removeRequest(o.tId);
        var url = o.status ? o.getResponseHeader["X-Debug-URL"] : undefined;
        if (url) {
            window.location = url;
        } else {
            var data = YAHOO.lang.JSON.parse(o.responseText);
            YAHOO.kansha.app.syncError(data.status, data.details);
        }
    },

    success: function (o) {
        removeRequest(o.tId);
        if (o.responseText.substring(0, 1) !== "<") {
            setTimeout(o.responseText, 0);
            setTimeout(YAHOO.kansha.app.initTooltips, 10);
        } else {
            YAHOO.kansha.app.syncError(500, 'Must reload all');
        }
    },

    upload: function (o) {
        removeRequest(o.tId);
        if (o.responseText.substring(0, 5) !== "URL: ") {
            var js = "", i;
            var js_fragments = o.responseXML.lastChild.lastChild.firstChild;

            for (i = 0; i < js_fragments.childNodes.length; i++) {
                js += js_fragments.childNodes[i].data;
            }
            setTimeout(js, 0);
            setTimeout(YAHOO.kansha.app.initTooltips, 10);
        } else {
            var data = YAHOO.lang.JSON.parse(o.responseText);
            YAHOO.kansha.app.syncError(data.status, data.details);
        }
    }
};

// Callers
function nagare_getAndEval(href) {
    var actionId = /_action([0-9]+)/.exec(href)[1];
    YAHOO.util.Connect.initHeader("ACCEPT", NAGARE_CONTENT_TYPE);
    if (!hasRequest(actionId)) {
        var req = YAHOO.util.Connect.asyncRequest("GET", href, nagare_callbacks);
        addRequest(req.tId, actionId);
    }
    return false;
}

function nagare_hasUpload(f) {
    var inputs = f.getElementsByTagName("input"),
        i;
    for (i = 0; i < inputs.length; i++) {
        if (inputs[i].getAttribute("type") === "file") {
            return true;
        }
    }
    return false;
}

function nagare_postAndEval(f, action) {
    var actionId = /_action([0-9]+)/.exec(action)[1];
    YAHOO.util.Connect.initHeader("ACCEPT", NAGARE_CONTENT_TYPE);
    YAHOO.util.Connect.setForm(f, nagare_hasUpload(f));
    if (!hasRequest(actionId)) {
        var req = YAHOO.util.Connect.asyncRequest("POST", "?_a&" + action, nagare_callbacks);
        addRequest(req.tId, actionId);
    }
    return false;
}

function nagare_imageInputSubmit(event, button, action) {
    var evt = event || window.event;
    var xy = YAHOO.util.Dom.getXY(button);
    return nagare_postAndEval(button.form, action + ".x=" + (evt.clientX - xy[0]) + "&" + action + ".y=" + (evt.clientY - xy[1]));
}
