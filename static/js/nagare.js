//--
// Copyright (c) 2012, Net-ng.
// All rights reserved.
//
// This software is licensed under the BSD License, as described in
// the file LICENSE.txt, which you should have received as part of
// this distribution.
//--

var nagare_ongoing_request = false;
var nagare_chain = [];


// Callbacks
nagare_callbacks = {
    failure: function (o) {
        nagare_ongoing_request = false;
        var url = o.status ? o.getResponseHeader["X-Debug-URL"] : undefined;
        if (url) {
            window.location = url;
        } else {
            var data = YAHOO.lang.JSON.parse(o.responseText);
            YAHOO.kansha.app.syncError(data.status, data.details);
        }
    },

    success: function (o) {
        nagare_ongoing_request = false;
        YAHOO.kansha.app.hideWaiter();
        if (o.responseText.substring(0, 1) !== "<") {
            eval(o.responseText);
            nagare_call_next();
        } else {
            nagare_ongoing_request = true;
            YAHOO.kansha.app.syncError(500, 'Must reload all');
        }
    },

    upload: function (o) {
        nagare_ongoing_request = false;
        if (o.responseText.substring(0, 5) !== "URL: ") {
            var js = "", i;
            var js_fragments = o.responseXML.lastChild.lastChild.firstChild;

            for (i = 0; i < js_fragments.childNodes.length; i++) {
                js += js_fragments.childNodes[i].data;
            }
            setTimeout(js, 0);
        } else {
            var data = YAHOO.lang.JSON.parse(o.responseText);
            nagare_ongoing_request = true;
            YAHOO.kansha.app.syncError(data.status, data.details);
        }
    }
};

function nagare_chained_calls(func_array) {
    nagare_chain = func_array;
    nagare_call_next();
}

function nagare_call_next() {
    if (nagare_chain.length > 0) {
        var next = nagare_chain.shift();
        next();
    }
}

// Callers
function nagare_getAndEval(href) {
    YAHOO.util.Connect.initHeader("ACCEPT", NAGARE_CONTENT_TYPE);
    if (!nagare_ongoing_request) {
        var req = YAHOO.util.Connect.asyncRequest("GET", href, nagare_callbacks);
        nagare_ongoing_request = true;
    } else {
        YAHOO.kansha.app.showWaiter();
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
    YAHOO.util.Connect.initHeader("ACCEPT", NAGARE_CONTENT_TYPE);
    YAHOO.util.Connect.setForm(f, nagare_hasUpload(f));
    if (!nagare_ongoing_request) {
        var req = YAHOO.util.Connect.asyncRequest("POST", "?_a&" + action, nagare_callbacks);
        nagare_ongoing_request = true;
    } else {
        YAHOO.kansha.app.showWaiter();
    }
    return false;
}

function nagare_imageInputSubmit(event, button, action) {
    var evt = event || window.event;
    var xy = YAHOO.util.Dom.getXY(button);
    return nagare_postAndEval(button.form, action + ".x=" + (evt.clientX - xy[0]) + "&" + action + ".y=" + (evt.clientY - xy[1]));
}
