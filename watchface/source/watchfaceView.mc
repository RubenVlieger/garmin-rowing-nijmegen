using Toybox.WatchUi;
using Toybox.Graphics;
using Toybox.System;
using Toybox.Lang;
using Toybox.Application;
using Toybox.Time;
using Toybox.Time.Gregorian;

class watchfaceView extends WatchUi.WatchFace 
{
    // --- Data Storage ---
    private var weatherData;  
    private var isStale = true;
    private var bgImage;
    private var showBackground = true; // New Setting Variable

    // --- Layout Coordinates ---
    private var cx, cy, width, height;
    private var batteryY, dateY, timeY;
    private var dashY, windY, waterY;
    private var windStartX, windStep;
    private var imgX = 0, imgY = 0;

    // --- Cache Variables ---
    private var lastDateDay = -1;
    private var cachedDateStr = "";
    private var lastTimeMin = -1;
    private var cachedTimeStr = "";
    private var lastBatteryVal = -1.0;
    private var cachedBatteryStr = "";

    function initialize() {
        WatchFace.initialize();
        updateWeatherData(); 
    }

    function onLayout(dc as Graphics.Dc) as Void {
        // 1. Check Settings first
        try {
            showBackground = Application.Properties.getValue("ShowBackgroundImage");
        } catch (ex) {
            showBackground = true; // Default to true if setting fails
        }

        // 2. Load Resources
        if (showBackground) {
            try {
                if (bgImage == null) { // Don't reload if already loaded
                    bgImage = Application.loadResource(Rez.Drawables.LauncherBackground);
                }
            } catch (ex) {
                bgImage = null;
            }
        } else {
            bgImage = null; // Free memory if setting is off
        }

        // 3. Calculate Screen Geometry
        width = dc.getWidth();
        height = dc.getHeight();
        cx = width / 2;
        cy = height / 2;

        if (bgImage != null) {
            imgX = (width - bgImage.getWidth()) / 2;
            imgY = (height - bgImage.getHeight()) / 2;
        }

        batteryY = height * 0.10;
        dateY    = height * 0.18;
        timeY    = height * 0.27;
        
        dashY    = height * 0.70;
        windY    = dashY + (height * 0.07);
        waterY   = windY + (height * 0.09);

        var totalWindWidth = width * 0.40;
        windStep = totalWindWidth / 3;
        windStartX = cx - (totalWindWidth / 2);
    }

    function onShow() as Void {
        updateWeatherData();
    }

    function updateWeatherData() as Void {
        var data = Application.Storage.getValue("weather_data");
        
        if (data instanceof Lang.Array && data.size() >= 12) {
            weatherData = data;
            
            var dataTime = data[0];
            if (dataTime != null && (Time.now().value() - dataTime) < 7200) {
                isStale = false;
            } else {
                isStale = true;
            }
        } else {
            weatherData = null;
            isStale = true;
        }
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        
        // 1. Draw Background
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear(); 
        
        // Only draw bitmap if setting is enabled AND image loaded
        if (showBackground && bgImage != null) {
            dc.drawBitmap(imgX, imgY, bgImage);
        }

        // 2. Parse Weather Data
        var waterNow = 0, waterTmr = 0, precip = 0.0, sunScore = 5, fogScore = 5, currentTemp = 0;
        var winds = [0, 0, 0, 0]; 

        if (weatherData != null) {
            waterNow = weatherData[1] != null ? weatherData[1] : 0;
            waterTmr = weatherData[2] != null ? weatherData[2] : 0;
            precip   = weatherData[3] != null ? weatherData[3] : 0.0;
            winds    = [weatherData[4], weatherData[5], weatherData[6], weatherData[8]]; 
            sunScore = weatherData[9] != null ? weatherData[9] : 5;
            fogScore = weatherData[10] != null ? weatherData[10] : 5;
            currentTemp = weatherData[11]; 
        }

        // 3. TOP SECTION: Battery & Date
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        
        var stats = System.getSystemStats();
        if (stats.battery != lastBatteryVal) {
            cachedBatteryStr = stats.battery.format("%d") + "%";
            lastBatteryVal = stats.battery;
        }
        dc.drawText(cx, batteryY, Graphics.FONT_XTINY, cachedBatteryStr, Graphics.TEXT_JUSTIFY_CENTER);

        var now = Time.now();
        var info = Gregorian.info(now, Time.FORMAT_MEDIUM);
        if (info.day != lastDateDay) {
            cachedDateStr = Lang.format("$1$ $2$", [info.day, info.month]);
            lastDateDay = info.day;
        }
        dc.drawText(cx, dateY, Graphics.FONT_XTINY, cachedDateStr, Graphics.TEXT_JUSTIFY_CENTER);

        // 4. CENTER: Time
        var clockTime = System.getClockTime();
        if (clockTime.min != lastTimeMin) {
            cachedTimeStr = Lang.format("$1$:$2$", [clockTime.hour.format("%02d"), clockTime.min.format("%02d")]);
            lastTimeMin = clockTime.min;
        }
        
        dc.setColor(isStale ? Graphics.COLOR_LT_GRAY : Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, timeY, Graphics.FONT_NUMBER_HOT, cachedTimeStr, Graphics.TEXT_JUSTIFY_CENTER);

        // 5. BOTTOM SECTION
        var statusStr = precip.format("%.1f") + "mm";
        if (sunScore >= 8) { statusStr += "  SUN"; }
        if (fogScore <= 3) { statusStr += "  FOG"; }
        
        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, dashY, Graphics.FONT_XTINY, statusStr, Graphics.TEXT_JUSTIFY_CENTER);

        for (var i = 0; i < 4; i++) {
            drawWindValue(dc, windStartX + (windStep * i), windY, winds[i]);
        }

        var trend = "=";
        if (waterTmr - waterNow >= 50) { trend = "^"; }
        else if (waterNow - waterTmr > 50) { trend = "v"; }
        
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