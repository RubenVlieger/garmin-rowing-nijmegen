using Toybox.WatchUi;
using Toybox.Graphics;
using Toybox.System;
using Toybox.Lang;
using Toybox.Application;
using Toybox.Time;
using Toybox.Time.Gregorian;

class watchfaceView extends WatchUi.WatchFace {
    
    private var bgImage;

    function initialize() {
        WatchFace.initialize();
    }

    function onLayout(dc as Graphics.Dc) as Void {
        try {
            bgImage = Application.loadResource(Rez.Drawables.LauncherBackground);
        } catch (ex) {
            bgImage = null;
        }
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();
        
        if (bgImage != null) {
            dc.drawBitmap(0, 0, bgImage);
        }

        // 1. Fetch Data
        var data = Application.Storage.getValue("weather_data");
        var waterNow = 0, waterTmr = 0, precip = 0.0, sunScore = 5, fogScore = 5;
        var winds = [0, 0, 0, 0]; // Now, +1, +2, Tmr9
        var isStale = true;

        if (data instanceof Lang.Array && data.size() >= 11) {
            waterNow = data[1] != null ? data[1] : 0;
            waterTmr = data[2] != null ? data[2] : 0;
            precip   = data[3] != null ? data[3] : 0.0;
            winds    = [data[4], data[5], data[6], data[8]]; // Note: data[8] is Tmr@9
            sunScore = data[9] != null ? data[9] : 5;
            fogScore = data[10] != null ? data[10] : 5;
            
            var dataTime = data[0];
            if (dataTime != null && (Time.now().value() - dataTime) < 7200) {
                isStale = false;
            }
        }

        // 2. TOP SECTION: Battery & Date
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        var stats = System.getSystemStats();
        var dateInfo = Gregorian.info(Time.now(), Time.FORMAT_MEDIUM);
        var dateStr = Lang.format("$1$ $2$", [dateInfo.day, dateInfo.month]);
        
        dc.drawText(130, 25, Graphics.FONT_XTINY, stats.battery.toNumber().toString() + "%", Graphics.TEXT_JUSTIFY_CENTER);
        dc.drawText(130, 45, Graphics.FONT_XTINY, dateStr, Graphics.TEXT_JUSTIFY_CENTER);

        // 3. CENTER: Time
        var clockTime = System.getClockTime();
        var timeStr = Lang.format("$1$:$2$", [clockTime.hour.format("%02d"), clockTime.min.format("%02d")]);
        dc.setColor(isStale ? Graphics.COLOR_LT_GRAY : Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(130, 70, Graphics.FONT_NUMBER_HOT, timeStr, Graphics.TEXT_JUSTIFY_CENTER);

        // 4. BOTTOM 30% (The Dashboard)
        var dashY = 140;

        // Water Level + Trend
        var trend = "=";
        if (waterTmr - waterNow >= 50) { trend = "^"; } // Using ^ for "Up" per your logic
        else if (waterNow - waterTmr > 50) { trend = "v"; } // Using v for "Down"
        
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(130, 220, Graphics.FONT_TINY, waterNow + "m
        m " + trend, Graphics.TEXT_JUSTIFY_CENTER);

        // Wind Strip (Now, +1h, +2h, Tmr9)
        var xOffsets = [75, 110, 145, 185];
        for (var i = 0; i < 4; i++) {
            drawWindValue(dc, xOffsets[i], dashY + 63, winds[i]);
        }

        // Precip, Sun, Fog Indicators
        var statusStr = precip.format("%.1f") + "mm";
        if (sunScore >= 8) { statusStr += "  SUN"; }
        if (fogScore <= 3) { statusStr += "  FOG"; }
        
        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(130, dashY + 45, Graphics.FONT_XTINY, statusStr, Graphics.TEXT_JUSTIFY_CENTER);
    }

    private function drawWindValue(dc as Graphics.Dc, x as Lang.Number, y as Lang.Number, knots as Lang.Number) as Void {
        var color = 0xFFFFFF;
        if (knots < 6) { color = 0xAA00FF; } 
        else if (knots < 13) { color = 0x0000FF; } 
        else if (knots < 25) { color = 0x00FFFF; } 
        else if (knots < 35) { color = 0x00FF00; } 
        else if (knots < 50) { color = 0xFFFF00; } 
        else { color = 0xFF0000; }

        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(x, y, Graphics.FONT_XTINY, knots.toString(), Graphics.TEXT_JUSTIFY_CENTER);
    }
}