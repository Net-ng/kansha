(function() {
    $(function() {
        var $container = $('#search'),
            $search = $container.find('input'),
            $searchIcon = $container.find('.search_icon'),
            $closeIcon = $container.find('.search_close');
        $closeIcon.click(function() {
            $search.val('');
            $search.trigger('input');
            $searchIcon.show();
            $closeIcon.hide();
        });
        $search.keyup(function(e) {
            if ($(this).val()) {
                $searchIcon.hide();
                $closeIcon.show();
            } else {
                $searchIcon.show();
                $closeIcon.hide();
            }
        });
    });
}());