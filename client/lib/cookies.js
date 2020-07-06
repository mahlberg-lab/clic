

function getCookie(name) {
	var value = "; " + document.cookie;
	var parts = value.split("; " + name + "=");
	if (parts.length == 2) return parts.pop().split(";").shift();
}


function x() {
    document.cookie = 'testCookie=testValue; expires=Fri, 31 Dec 2024 23:59:59 GMT';

    console.log(getCookie('test'));
}

module.exports = x;
