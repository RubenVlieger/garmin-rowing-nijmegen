using Toybox.Background;
using Toybox.System;
using Toybox.Communications;
using Toybox.Application.Storage;

// The Service Delegate that handles the background task
(:background)
class BackgroundService extends System.ServiceDelegate {

    function initialize() {
        ServiceDelegate.initialize();
    }

    function onTemporalEvent() {
        // REPLACE THIS URL with your raw GitHub user content URL
        var url = "https://raw.githubusercontent.com/RubenVlieger/garmin-rowing-nijmegen/main/data.json";
        
        var options = {
            :method => Communications.HTTP_REQUEST_METHOD_GET,
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        };

        Communications.makeWebRequest(url, {}, options, method(:onReceive));
    }

    function onReceive(responseCode, data) {
        if (responseCode == 200) {
            Background.exit(data); // Send data back to the App
        } else {
            Background.exit(null); // Failed
        }
    }
}