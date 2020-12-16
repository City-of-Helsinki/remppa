/**
 * Initialize polling timers
 */
function init() {
    change();
    setInterval(change, 1000);
    setInterval(update_state, 1000);
}

var small_url;
var crop_url;

/**
 * Change thumbnail images, fool caching by introducing random numbers
 */
function change() {
   document.getElementById("small").src = small_url + "?r=" + Math.random();
   document.getElementById("crop").src = crop_url + "?r=" + Math.random();
}

var update_url;
/**
 * Request Stringified JSON from server updating the current view.
 */
function update_state() {
    var xhr = new XMLHttpRequest();
    if (xhr.upload) {
        // file received/failed
        xhr.onreadystatechange = function(e) {
            if (xhr.readyState == 4) {
                if (xhr.status == 200) {
                    document.getElementById("state_view").innerHTML = xhr.response;
                } else {
                    console.log(xhr.response);
                }
            }
        };

        // start upload
        xhr.open("GET", update_url, true);
        xhr.send();

    }
}



