"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */

function getCookie(name) {
    // Convert cookies string to list
    var c_list = document.cookie.split("; "),
        i = 0,
        c,
        c_name,
        c_value;
    // Loop through cookies list to find a match
    for (i = 0; i < c_list.length; i++) {
        // Find cookie
        c = c_list[i].split('=');
        c_name = c[0];
        c_value = c[1];
        // Return cookie value if cookie name matches
        if (c_name === name) {
            return c_value;
        }
    }
    // If no cookie found with given name, return null
    return null;
}


// Show a message about cookies to user if they have not yet agreed
function showCookieMessage() {

    document.cookie = '';

    // If user hasn't yet agreed to cookies
    if (getCookie('cookieMessageApprove') !== '1') {

        // Generate HTML message
        var html_to_inject = '\
<div id="cookie-message-popup" style="text-align: center; z-index: 10000; background: black; width: 96vw; padding: 1em; color: white; position: fixed; bottom: 2vw; right: 2vw;">\
    The CLiC website uses cookies. By using the CLiC website, you accept our use of cookies. See our <a href="/cookies/" style="color: white; text-decoration: underline;">cookies policy</a> for more information.\
    <button id="cookie-message-popup-accept" style="display: inline-block; background: white; color: black; padding: 0.4em 1.7em; margin-left: 1em; cursor: pointer; vertical-align: middle;">Accept</button>\
</div>';

        // Add the HTML message to the page
        document.body.innerHTML += html_to_inject;
    }

    // Add event listener for 'accept' button to set the cookie and hide the message
    document.getElementById("cookie-message-popup-accept").addEventListener("click", function () {
        document.cookie = "cookieMessageApprove=1; expires=Mon, 31 Dec 2040 23:59:59 GMT";
        document.getElementById("#cookie-message-popup").style.display = "none";
    });
}

module.exports = showCookieMessage;
