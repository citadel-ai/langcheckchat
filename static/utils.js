/*************************************************************************
* Utils
*************************************************************************/

// Round a float to even with decimal places
// Rounding logic: https://stackoverflow.com/a/49080858
function round(n, places) {
    if (typeof n !== 'number' || Number.isInteger(n)) { return n; }
    var x = n * Math.pow(10, places);
    var r = Math.round(x);
    // Account for precision using Number.EPSILON
    var br = (Math.abs(x) % 1 > 0.5 - Number.EPSILON && Math.abs(x) % 1 < 0.5 + Number.EPSILON) ? (r % 2 === 0 ? r : r - 1) : r;
    return br / Math.pow(10, places);
}

// Replace certain characters with HTML entities
function escapeHTML(str) {
    return str.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
}
