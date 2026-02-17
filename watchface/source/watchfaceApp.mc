using Toybox.Application;
using Toybox.Time;
using Toybox.Background;
using Toybox.System;
using Toybox.Lang;
using Toybox.WatchUi;


class watchfaceApp extends Application.AppBase {

    function initialize() {
        AppBase.initialize();
    }

    function onStart(state as Lang.Dictionary?) as Void {
        if (Toybox.System has :ServiceDelegate) {
            try {
                Background.registerForTemporalEvent(new Time.Duration(3600));
                System.println("Background service registered for hourly updates");
            } catch (ex) {
                System.println("Failed to register background service: " + ex.getErrorMessage());
            }
        } else {
            System.println("Background service not supported on this device");
        }
    }

    function onStop(state as Lang.Dictionary?) as Void {
    }

    function getInitialView() {
        return [new watchfaceView()];
    }

    function getServiceDelegate() {
        return [new BackgroundService()];
    }

    function onBackgroundData(data as Application.PersistableType) as Void {
        if (data != null) {
            Application.Storage.setValue("weather_data", data);
            WatchUi.requestUpdate();
        }
    }
}