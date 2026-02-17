using Toybox.Background;
using Toybox.System;
using Toybox.Communications;
using Toybox.Application.Storage;
using Toybox.Lang;

(:background)
class BackgroundService extends System.ServiceDelegate {

    function initialize() {
        ServiceDelegate.initialize();
    }

    function onTemporalEvent() {
        var url = "https://raw.githubusercontent.com/RubenVlieger/garmin-rowing-nijmegen/main/data.json";
        var options = {
            :method => Communications.HTTP_REQUEST_METHOD_GET,
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        };
        
        Communications.makeWebRequest(url, {}, options, method(:onReceive));
    }

    function onReceive(responseCode as Lang.Number, data as Lang.Any) as Void {
        if (responseCode == 200 && data instanceof Lang.Array) {
            // data is the JSON array from data.json
            Background.exit(data);
        } else {
            System.println("Request failed or invalid data: " + responseCode);
            Background.exit(null);
        }
    }
}