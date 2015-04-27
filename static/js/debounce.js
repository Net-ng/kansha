/**
 * Ensure the callback `cb` is called once within delay on element elt
 * uses jQuery
 */
function debounce(elt, cb, delay) {
    var $this = $(elt);

    clearTimeout($this.data('timeout'));

    $this.data('timeout', setTimeout(function(){
        cb(elt);
    }, delay));
}