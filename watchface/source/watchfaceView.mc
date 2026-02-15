using Toybox.WatchUi;
using Toybox.Graphics;
using Toybox.System;
using Toybox.Lang;
using Toybox.Application;
using Toybox.Time;

class watchfaceView extends WatchUi.WatchFace {
    
    var bgImage;

    function initialize() {
        WatchFace.initialize();
    }

    function onLayout(dc) {
        // Load your dithered image here
        bgImage = Application.loadResource(Rez.Drawables.LauncherBackground);
    }

    function onUpdate(dc) {
        // 1. Draw Background
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();
        if (bgImage != null) {
            dc.drawBitmap(0, 0, bgImage);
        }

        // 2. Get Data from Storage
        var data = Application.Storage.getValue("weather_data");
        
        // Default values if no data exists yet
        var windNow = 0; var windP1 = 0; var windP2 = 0; var windP3 = 0;
        var waterNow = 0; var precip = 0.0;
        var isStale = false;

        if (data instanceof Toybox.Lang.Array && data.size() >= 11) {
            // Mapping based on your Python script 
            // [0:Time, 1:WaterNow, 2:WaterTmr, 3:Precip, 4:WindNow, 5:W+1, 6:W+2, 7:W+3, 8:WTmr, 9:Sun, 10:Fog]
            
            var dataTime = data[0];
            waterNow = data[1];
            precip = data[3];
            windNow = data[4];
            windP1 = data[5];
            windP2 = data[6];
            windP3 = data[7];
            
            // Stale Data Check (Current time - Data time > 2 hours)
            var nowEpoch = Time.now().value();
            if ((nowEpoch - dataTime) > 7200) { isStale = true; }
        }

        // 3. Draw Time (Big, Center)
        var clockTime = System.getClockTime();
        var timeString = Lang.format("$1$:$2$", [clockTime.hour, clockTime.min.format("%02d")]);
        
        dc.setColor(isStale ? Graphics.COLOR_LT_GRAY : Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(130, 80, Graphics.FONT_NUMBER_HOT, timeString, Graphics.TEXT_JUSTIFY_CENTER);

        // 4. Draw Wind Strip (The Horizon Line)
        var yWind = 150;
        // Draw 4 wind speeds next to each other
        drawWindValue(dc, 70, yWind, windNow);   // Now
        drawWindValue(dc, 110, yWind, windP1);   // +1h
        drawWindValue(dc, 150, yWind, windP2);   // +2h
        drawWindValue(dc, 190, yWind, windP3);   // +3h

        // 5. Draw Conditions (Water Level left, Precip right)
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        // Water Level (Left)
        dc.drawText(60, 190, Graphics.FONT_SYSTEM_TINY, waterNow + "cm", Graphics.TEXT_JUSTIFY_CENTER);
        // Precip (Right)
        if (precip > 0) {
            dc.drawText(200, 190, Graphics.FONT_SYSTEM_TINY, precip + "mm", Graphics.TEXT_JUSTIFY_CENTER);
        }
    }

    // Helper: Draws a wind number with your specific color coding 
    function drawWindValue(dc, x, y, knots) {
        var color = Graphics.COLOR_WHITE;
        
        if (knots < 6) { color = 0xAA00FF; }       // Purple
        else if (knots < 13) { color = 0x0000FF; } // Blue
        else if (knots < 25) { color = 0x00FFFF; } // Cyan
        else if (knots < 35) { color = 0x00FF00; } // Green
        else if (knots < 43) { color = 0x005500; } // DkGreen
        else if (knots < 50) { color = 0xFFFF00; } // Yellow
        else if (knots < 60) { color = 0xFFAA00; } // Orange
        else { color = 0xFF0000; }                 // Red

        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(x, y, Graphics.FONT_SYSTEM_SMALL, knots.toString(), Graphics.TEXT_JUSTIFY_CENTER);
    }

    function onHide() {
    }
    function onExit() {
    }
}