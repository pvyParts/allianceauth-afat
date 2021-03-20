/**
 * convert a string to a slug
 * @param text
 * @returns {string}
 */
function convertStringToSlug(text) {
    'use strict';

    return text.toLowerCase().replace(/[^\w ]+/g,'').replace(/ +/g,'-');
}

function sortTable(table, order) {
    'use strict';

    let asc   = order === 'asc';
    let tbody = table.find('tbody');

    tbody.find('tr').sort(function(a, b) {
        if (asc) {
            return $('td:first', a).text().localeCompare($('td:first', b).text());
        } else {
            return $('td:first', b).text().localeCompare($('td:first', a).text());
        }
    }).appendTo(tbody);
}
