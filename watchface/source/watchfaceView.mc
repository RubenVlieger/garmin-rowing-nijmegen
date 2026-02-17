using Toybox.WatchUi;
using Toybox.Graphics;
using Toybox.System;
using Toybox.Lang;
using Toybox.Application;
using Toybox.Time;
using Toybox.Time.Gregorian;

class watchfaceView extends WatchUi.WatchFace 
{
    
    private var bgImage;
    private var weatherData;  // cache, for battery efficiency
    private var isStale = true;

    function initialize() {
        WatchFace.initialize();
        // Load data immediately on startup
        updateWeatherData(); 
    }

    function onLayout(dc as Graphics.Dc) as Void {
        try {
            bgImage = Application.loadResource(Rez.Drawables.LauncherBackground);
        } catch (ex) {
            bgImage = null;
        }
    }

    // Called when the watch face comes out of sleep or app starts
    function onShow() as Void {
        updateWeatherData();
    }

    // Helper to load from storage (saves battery vs calling in onUpdate)
    function updateWeatherData() as Void {
        var data = Application.Storage.getValue("weather_data");
        
        if (data instanceof Lang.Array && data.size() >= 11) {
            weatherData = data;
            
            var dataTime = data[0];
            // Check if data is older than 2 hours (7200 seconds)
            if (dataTime != null && (Time.now().value() - dataTime) < 7200) {
                isStale = false;
            } else {
                isStale = true;
            }
        } else {
            weatherData = null;
        }
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        var width = dc.getWidth();
        var height = dc.getHeight();
        var cx = width / 2; // Center X
        
        // 1. Draw Background
        // dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        // dc.clear();
        
        if (bgImage != null) {
            var imgW = bgImage.getWidth();
            var imgH = bgImage.getHeight();

            // Center the image if it doesn't match screen size exactly, 
            // or just draw at 0,0 if it's the right size.
            // For best results, use a background that matches the largest resolution 
            // or a solid color background. Here we just draw at 0,0.
            var x = (width - imgW) / 2;
            var y = (height - imgH) / 2;
            
            // Draw centered
            dc.drawBitmap(x, y, bgImage);
         }

        // 2. Parse Cached Data
        var waterNow = 0, waterTmr = 0, precip = 0.0, sunScore = 5, fogScore = 5, currentTemp = 0;
        var winds = [0, 0, 0, 0]; // Now, +1, +2, Tmr9

        if (weatherData != null) {
            waterNow = weatherData[1] != null ? weatherData[1] : 0;
            waterTmr = weatherData[2] != null ? weatherData[2] : 0;
            precip   = weatherData[3] != null ? weatherData[3] : 0.0;
            winds    = [weatherData[4], weatherData[5], weatherData[6], weatherData[8]]; 
            sunScore = weatherData[9] != null ? weatherData[9] : 5;
            fogScore = weatherData[10] != null ? weatherData[10] : 5;
        }
        if (weatherData != null && weatherData.size() >= 12) {
            currentTemp = weatherData[11]; // This is the new value
        }

        // 3. TOP SECTION: Battery & Date
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        var stats = System.getSystemStats();
        var dateInfo = Gregorian.info(Time.now(), Time.FORMAT_MEDIUM);
        var dateStr = Lang.format("$1$ $2$", [dateInfo.day, dateInfo.month]);
        
        // Dynamic Y positions: 10% and 18% down the screen
        dc.drawText(cx, height * 0.10, Graphics.FONT_XTINY, stats.battery.toNumber().toString() + "%", Graphics.TEXT_JUSTIFY_CENTER);
        dc.drawText(cx, height * 0.18, Graphics.FONT_XTINY, dateStr, Graphics.TEXT_JUSTIFY_CENTER);

        // 4. CENTER: Time
        var clockTime = System.getClockTime();
        var timeStr = Lang.format("$1$:$2$", [clockTime.hour.format("%02d"), clockTime.min.format("%02d")]);
        dc.setColor(isStale ? Graphics.COLOR_LT_GRAY : Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        
        // Time at roughly 30% down
        dc.drawText(cx, height * 0.27, Graphics.FONT_NUMBER_HOT, timeStr, Graphics.TEXT_JUSTIFY_CENTER);

        // 5. BOTTOM SECTION (The Dashboard)
        // We start the dashboard around 65% down the screen
        var dashY = height * 0.7; 

        // Precip, Sun, Fog Indicators
        var statusStr = precip.format("%.1f") + "mm";
        if (sunScore >= 8) { statusStr += "  SUN"; }
        if (fogScore <= 3) { statusStr += "  FOG"; }
        
        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, dashY, Graphics.FONT_XTINY, statusStr, Graphics.TEXT_JUSTIFY_CENTER);

        // Wind Strip (Now, +1h, +2h, Tmr9)
        // Dynamically calculate spacing based on screen width
        // We want the 4 wind numbers to span about 60% of the screen width
        var totalWindWidth = width * 0.40;
        var step = totalWindWidth / 3; // 3 gaps between 4 items
        var startX = cx - (totalWindWidth / 2);
        
        var windY = dashY + (height * 0.07); // Slightly below precipitation

        for (var i = 0; i < 4; i++) {
            drawWindValue(dc, startX + (step * i), windY, winds[i]);
        }

        // Water Level + Trend
        var trend = "=";
        if (waterTmr - waterNow >= 50) { trend = "^"; }
        else if (waterNow - waterTmr > 50) { trend = "v"; }
        
        var waterY = windY + (height * 0.09); // Below wind
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);

        var bottomInfo = Lang.format("$1$ $2$ $3$C", [waterNow, trend, currentTemp]);
        dc.drawText(cx, waterY, Graphics.FONT_XTINY, bottomInfo, Graphics.TEXT_JUSTIFY_CENTER);
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