/**
 * Very simple basic rule set
 *
 * Allows
 *    <i>, <em>, <b>, <strong>, <p>, <div>, <a href="http://foo"></a>, <br>, <span>, <ol>, <ul>, <li>
 *
 * For a proper documentation of the format check advanced.js
 */
var wysihtmlParserRules = {
  tags: {
    strong: {},
    b:      {},
    i:      {},
    em:     {},
    u:      {},
    br:     {},
    p:      {},
    div:    {},
    span:   {},
    ul:     {},
    ol:     {},
    li:     {},
    a:      {
      set_attributes: {
        target: "_blank",
        rel:    "nofollow"
      },
      check_attributes: {
        href:   (function() {
          var REG_EXP = /^(#|\/|https?:\/\/|mailto:|tel:|file:\/\/)/i;
          return function(attributeValue) {
            if (!attributeValue || !attributeValue.match(REG_EXP)) {
              return null;
            }
            return attributeValue.replace(REG_EXP, function(match) {
              return match.toLowerCase();
            });
          };
        })()
      }
    }
  }
};
