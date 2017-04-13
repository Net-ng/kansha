$(function () {
    var $checklists = $('.checklists'),
        nbChecklists = $checklists.find('.checklist').length;
    $checklists.sortable({
        placeholder: "ui-state-highlight",
        handle: ".icon-list",
        cursor: "move",
        start: function (e, ui) {
            ui.placeholder.height(ui.item.height());
        },
        stop: function (event, ui) {
            reorder_checklists($('.checklist').map(function () {
                return this.id;
            }).get());
        }
    });

    // Disable sortable if only contains 1 item
    if (nbChecklists == 1) {
        $checklists.sortable('disable');
    } else if (nbChecklists > 1) {
        $checklists.sortable('enable');
    }

    var $checklistItems = $(".checklists .checklist .content ul");
    $checklistItems.sortable({
        placeholder: "ui-state-highlight",
        cursor: "move",
        connectWith: ".checklists .checklist .content ul",
        dropOnEmpty: true,
        handle: ".not-alone",
        start: function (e, ui) {
            ui.placeholder.height(ui.item.height());
        },
        update: function (event, ui) {
            var data = {
                target: ui.item.closest('.checklist').attr('id'),
                index: ui.item.index(),
                id: ui.item.attr('id')
            };
            reorder_checklists_items(data);
        }
    }).disableSelection();

    // Disable sortable if only contains 1 item
    $checklistItems.each(function(index, elem) {
        var $elem = $(elem),
            nbChecklistItems = $elem.find('>li').length;
        if (nbChecklistItems == 1) {
            $elem.sortable('disable');
        } else if (nbChecklistItems > 1) {
            $elem.sortable('enable');
        }
    });
});