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

    // --- Bottom Section Cache ---
    private var cachedStatusStr = "";
    private var cachedBottomInfo = "";
    private var cachedWinds = [0, 0, 0, 0];

    // --- Rainbow Colors ---
    private const RAINBOW = [0xFF0000, 0xFF8800, 0xFFFF00, 0x00FF00, 0x0088FF, 0xAA00FF];

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

            // Pre-cache bottom section strings so onUpdate doesn't rebuild them every frame
            var waterNow = data[1] != null ? data[1] : 0;
            var waterTmr = data[2] != null ? data[2] : 0;
            var precip   = data[3] != null ? data[3] : 0.0;
            var sunScore = data[9] != null ? data[9] : 5;
            var fogScore = data[10] != null ? data[10] : 5;
            var currentTemp = data[11];

            cachedWinds = [data[4], data[5], data[6], data[8]];

            // Status string: precipitation (only if non-zero) + sun/fog indicators
            var s = "";
            if (precip != 0.0) {
                s = precip.format("%.1f") + "mm";
            }
            if (sunScore >= 8) { s += s.length() > 0 ? "  SUN" : "SUN"; }
            if (fogScore <= 3) { s += s.length() > 0 ? "  FOG" : "FOG"; }
            cachedStatusStr = s;

            // Bottom info: water level only when outside normal range (900–1150)
            var trend = "=";
            if (waterTmr - waterNow >= 50) { trend = "^"; }
            else if (waterNow - waterTmr > 50) { trend = "v"; }

            if (waterNow > 1150 || waterNow < 900) {
                cachedBottomInfo = Lang.format("$1$ $2$ $3$C", [waterNow, trend, currentTemp]);
            } else {
                cachedBottomInfo = currentTemp + "C";
            }
        } else {
            weatherData = null;
            isStale = true;
            cachedStatusStr = "";
            cachedBottomInfo = "";
            cachedWinds = [0, 0, 0, 0];
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

        // 2. TOP SECTION: Battery & Date
        var stats = System.getSystemStats();
        if (stats.battery != lastBatteryVal) {
            cachedBatteryStr = stats.battery.format("%d") + "%";
            lastBatteryVal = stats.battery;
        }

        // Draw battery icon (tiny rectangle + nub, ~6x4 px)
        var battTextW = dc.getTextWidthInPixels(cachedBatteryStr, Graphics.FONT_XTINY);
        var battTotalW = battTextW + 10; // icon width ~8 + 2px gap
        var battLeftX = cx - (battTotalW / 2);
        var iconY = batteryY + 5; // vertically center with text
        // Battery body
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.fillRoundedRectangle(battLeftX, iconY, 7, 4, 1);
        // Battery nub (positive terminal)
        dc.fillRectangle(battLeftX + 7, iconY + 1, 1, 2);

        // Battery text with color coding
        var battPct = stats.battery;
        var textX = battLeftX + 10;
        if (battPct > 90) {
            // Rainbow: draw each character in a different color
            drawRainbowText(dc, textX, batteryY, Graphics.FONT_XTINY, cachedBatteryStr);
        } else {
            if (battPct < 25) {
                dc.setColor(Graphics.COLOR_RED, Graphics.COLOR_TRANSPARENT);
            } else if (battPct < 40) {
                dc.setColor(Graphics.COLOR_ORANGE, Graphics.COLOR_TRANSPARENT);
            } else {
                dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
            }
            dc.drawText(textX, batteryY, Graphics.FONT_XTINY, cachedBatteryStr, Graphics.TEXT_JUSTIFY_LEFT);
        }

        // Date
        var now = Time.now();
        var info = Gregorian.info(now, Time.FORMAT_MEDIUM);
        if (info.day != lastDateDay) {
            cachedDateStr = Lang.format("$1$ $2$", [info.day, info.month]);
            lastDateDay = info.day;
        }
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, dateY, Graphics.FONT_XTINY, cachedDateStr, Graphics.TEXT_JUSTIFY_CENTER);

        // 3. CENTER: Time
        var clockTime = System.getClockTime();
        if (clockTime.min != lastTimeMin) {
            cachedTimeStr = Lang.format("$1$:$2$", [clockTime.hour.format("%02d"), clockTime.min.format("%02d")]);
            lastTimeMin = clockTime.min;
        }
        
        dc.setColor(isStale ? Graphics.COLOR_LT_GRAY : Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, timeY, Graphics.FONT_NUMBER_HOT, cachedTimeStr, Graphics.TEXT_JUSTIFY_CENTER);

        // 4. BOTTOM SECTION (uses cached strings from updateWeatherData)
        if (cachedStatusStr.length() > 0) {
            dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
            dc.drawText(cx, dashY, Graphics.FONT_XTINY, cachedStatusStr, Graphics.TEXT_JUSTIFY_CENTER);
        }

        if (weatherData != null) {
            for (var i = 0; i < 4; i++) {
                drawWindValue(dc, windStartX + (windStep * i), windY, cachedWinds[i]);
            }
        }

        if (cachedBottomInfo.length() > 0) {
            dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
            dc.drawText(cx, waterY, Graphics.FONT_XTINY, cachedBottomInfo, Graphics.TEXT_JUSTIFY_CENTER);
        }
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

    //! Draw text with rainbow-cycling colors (one color per character)
    private function drawRainbowText(dc as Graphics.Dc, x as Lang.Number, y as Lang.Number, font, text as Lang.String) as Void {
        var curX = x;
        for (var i = 0; i < text.length(); i++) {
            var ch = text.substring(i, i + 1);
            dc.setColor(RAINBOW[i % 6], Graphics.COLOR_TRANSPARENT);
            dc.drawText(curX, y, font, ch, Graphics.TEXT_JUSTIFY_LEFT);
            curX += dc.getTextWidthInPixels(ch, font);
        }
    }
}