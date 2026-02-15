using Toybox.Application;
using Toybox.Time;
using Toybox.Background;
using Toybox.System;

(:background)
class watchfaceApp extends Application.AppBase {

    function initialize() {
        AppBase.initialize();
    }

    function onStart(state) {
    }

    function onStop(state) {
    }

    // 1. Return the View
    function getInitialView() {
        // Register for temporal events if they are supported
        if(Toybox.System has :ServiceDelegate) {
            Background.registerForTemporalEvent(new Time.Duration(3600)); // 15 mins
        }
        return [ new watchfaceView() ];
    }

    // 2. Return the Background Service
    function getServiceDelegate() {
        return [ new BackgroundService() ];
    }

    // 3. Handle data coming back from the Background Service
    function onBackgroundData(data) {
        if (data != null) {
            Application.Storage.setValue("weather_data", data);
        }
    }
}