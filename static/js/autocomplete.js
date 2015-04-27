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
        NS = YAHOO.namespace('kansha.autocomplete');

    NS.init = function (field, completionUrl, delimiter, minQueryLength,
            maxResultsDisplayed, withWrapper) {
        var container = document.createElement('div');
        field = Dom.get(field);

        /* Update the DOM structure */
        if (withWrapper) {
            var wrapper = document.createElement('div');
            field.parentNode.appendChild(wrapper);
            wrapper.appendChild(container);
            wrapper.appendChild(field.parentNode.removeChild(field));
        } else {
            field.parentNode.appendChild(container);
        }

        /* Set the completion datasource */
        var dataSource = new YAHOO.util.XHRDataSource(completionUrl, {
            responseType: YAHOO.util.XHRDataSource.TYPE_JSARRAY,
            responseSchema: {fields: ['name', 'markup']}
        });

        /* Create and initialize the AutoComplete widget */
        var autoComplete = new YAHOO.widget.AutoComplete(field, container, dataSource, {
            animSpeed: 0.1,
            delimChar: delimiter,
            minQueryLength: minQueryLength,
            maxResultsDisplayed: maxResultsDisplayed,
            allowBrowserAutocomplete: false,
            generateRequest: function (query) {
                return query;
            },
            formatResult: function (oResultData, sQuery, sResultMatch) {
                var sMarkup = sResultMatch ? oResultData[1] : "";
                return sMarkup;
            }
        });

        return autoComplete;
    };
}());

