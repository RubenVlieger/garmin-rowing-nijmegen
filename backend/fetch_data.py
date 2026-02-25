import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import pytz
from io import StringIO

# --- CONFIGURATION ---
# Nijmegen coordinates
LAT = 51.847683
LON = 5.862825

# RWS Settings
RWS_API_URL = "https://ddapi20-waterwebservices.rijkswaterstaat.nl/ONLINEWAARNEMINGENSERVICES/OphalenWaarnemingen"

# Open-Meteo Settings (KNMI HARMONIE AROME)
OPEN_METEO_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=visibility,precipitation,weather_code,wind_speed_10m,temperature_2m&models=knmi_harmonie_arome_netherlands&timezone=auto&forecast_days=3"
# --- HELPER FUNCTIONS ---
def get_wind_color(knots):
    """Convert wind speed to color code (0-7)"""
    if knots < 6: return 0     # Purple
    if knots < 13: return 1    # Blue
    if knots < 25: return 2    # Cyan
    if knots < 35: return 3    # Green
    if knots < 43: return 4    # Dark Green
    if knots < 50: return 5    # Yellow
    if knots < 60: return 6    # Orange
    return 7                   # Red

def get_sun_score(weather_code):
    """
    Convert WMO weather code to sun score (0-10)
    WMO Codes: 0=clear, 1-3=partly cloudy, 45-48=fog, 51-67=rain, 71-86=snow, 95+=thunder
    """
    if weather_code is None:
        return 5
    
    wc = int(weather_code)
    
    # Clear sky
    if wc == 0:
        return 10
    # Mainly clear
    elif wc == 1:
        return 9
    # Partly cloudy
    elif wc == 2:
        return 7
    # Overcast
    elif wc == 3:
        return 4
    # Fog
    elif 45 <= wc <= 48:
        return 2
    # Rain/Snow/Thunder (cloudy)
    elif wc >= 51:
        return 1
    
    return 5  # Default

def get_fog_score(vis_m):
    """Convert visibility (meters) to fog score (0-10)"""
    if vis_m is None:
        return 5
    if vis_m >= 10000:
        return 10
    if vis_m >= 4000:
        return 8
    if vis_m >= 2000:
        return 6
    if vis_m >= 1000:
        return 4
    if vis_m >= 200:
        return 2
    return 0

# --- RWS FETCHER ---
# --- RWS DD-API 2.0 CONFIGURATION ---
RWS_API_URL = "https://ddapi20-waterwebservices.rijkswaterstaat.nl/ONLINEWAARNEMINGENSERVICES/OphalenWaarnemingen"

# --- RWS FETCHER ---
def fetch_rws_data(now_dt):
    """Fetch water level data from Rijkswaterstaat Lobith station via DD-API 2.0"""
    print(f"--- Fetching RWS Data (Lobith) via DD-API 2.0 ---")
    try:
        # We need data from 12 hours ago up to tomorrow to cover both "now" and "tomorrow 9:00"
        start_dt = now_dt - timedelta(hours=12)
        end_dt = now_dt + timedelta(days=2)
        
        # The DD-API requires strict ISO8601 strings (e.g., 2026-02-24T12:00:00.000+01:00)
        start_str = start_dt.isoformat(timespec='milliseconds')
        end_str = end_dt.isoformat(timespec='milliseconds')
        
        # Construct the JSON payload required by the new endpoint
        payload = {
            "Locatie": {"Code": "LOBI"},
            "AquoPlusWaarnemingMetadata": {
                "AquoMetadata": {
                    "Grootheid": {"Code": "WATHTE"}
                }
            },
            "Periode": {
                "Begindatumtijd": start_str,
                "Einddatumtijd": end_str
            }
        }

        # Make the POST request
        r = requests.post(RWS_API_URL, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        
        water_now = 0
        water_tmr = 0
        target_tmr = now_dt.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        metingen = []
        verwachtingen = []

        # Parse the JSON response
        if "WaarnemingenLijst" in data:
            for waarneming in data["WaarnemingenLijst"]:
                meta = waarneming.get("AquoPlusWaarnemingMetadata", {}).get("AquoMetadata", {})
                proces_type = meta.get("ProcesType", "").lower()
                
                meet_lijst = waarneming.get("MetingenLijst", [])
                
                for m in meet_lijst:
                    t_str = m.get("Tijdstip")
                    val = m.get("Meetwaarde", {}).get("Waarde_Numeriek")
                    if t_str and val is not None:
                        t_obj = datetime.fromisoformat(t_str)
                        # Separate historical measurements from future predictions
                        if proces_type == "meting":
                            metingen.append((t_obj, val))
                        elif proces_type == "verwacht":
                            verwachtingen.append((t_obj, val))
        
        # 1. Current Water Level (latest actual measurement before 'now_dt')
        metingen.sort(key=lambda x: x[0])
        past_metingen = [m for m in metingen if m[0] <= now_dt]
        if past_metingen:
            water_now = int(past_metingen[-1][1])
            
        # 2. Tomorrow 09:00 Prediction (closest prediction to target time)
        verwachtingen.sort(key=lambda x: x[0])
        if verwachtingen:
            closest_v = min(verwachtingen, key=lambda x: abs(x[0] - target_tmr))
            water_tmr = int(closest_v[1])

        print(f"✓ RWS DD-API Success: Now={water_now}cm, Tmr@9={water_tmr}cm")
        return water_now, water_tmr

    except Exception as e:
        print(f"✗ RWS Error: {e}")
        return 0, 0
    
    
# --- OPEN-METEO FETCHER ---
def fetch_weather_data(now_dt):
    """Fetch weather forecast from Open-Meteo (KNMI HARMONIE AROME)"""
    print(f"--- Fetching Weather Data (Open-Meteo / KNMI HARMONIE) ---")
    
    try:
        r = requests.get(OPEN_METEO_URL, timeout=15)
        r.raise_for_status()
        
        data = r.json()
        hourly = data['hourly']
        
        # Parse time array to datetime objects
        times = [datetime.fromisoformat(t) for t in hourly['time']]
        
        # Find index closest to current time
        current_idx = None
        min_diff = timedelta(hours=999)
        for i, t in enumerate(times):
            diff = abs(t - now_dt.replace(tzinfo=None))
            if diff < min_diff:
                min_diff = diff
                current_idx = i
        
        if current_idx is None:
            print("✗ Could not find current time in forecast data")
            return [0] * 8
        
        print(f"✓ Found current time: {times[current_idx]} (index {current_idx})")
        
        # Extract values
        wind_kmh = hourly['wind_speed_10m']
        precip_mm = hourly['precipitation']
        visibility_m = hourly['visibility']
        weather_codes = hourly['weather_code']
        temps_c = hourly['temperature_2m']
        
        # Helper to safely get value
        def safe_get(arr, idx, default=0):
            try:
                val = arr[idx] if idx < len(arr) else default
                return val if val is not None else default
            except:
                return default
        
        # Convert wind from km/h to knots (1 km/h = 0.539957 knots)
        def kmh_to_knots(kmh):
            return int(kmh * 0.539957) if kmh is not None else 0
        
        # Get wind values
        wind_now = kmh_to_knots(safe_get(wind_kmh, current_idx))
        wind_plus1 = kmh_to_knots(safe_get(wind_kmh, current_idx + 1))
        wind_plus2 = kmh_to_knots(safe_get(wind_kmh, current_idx + 2))
        wind_plus3 = kmh_to_knots(safe_get(wind_kmh, current_idx + 3))
        
        # Find tomorrow at 9:00
        target_tmr = now_dt.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        target_tmr = target_tmr.replace(tzinfo=None)
        
        tmr_idx = None
        min_tmr_diff = timedelta(hours=999)
        for i, t in enumerate(times):
            diff = abs(t - target_tmr)
            if diff < min_tmr_diff:
                min_tmr_diff = diff
                tmr_idx = i
        
        wind_tmr = kmh_to_knots(safe_get(wind_kmh, tmr_idx)) if tmr_idx else wind_now
        
        # Precipitation: sum of next 2 hours
        precip_next2h = round(
            safe_get(precip_mm, current_idx + 1, 0) + 
            safe_get(precip_mm, current_idx + 2, 0),
            1
        )
        
        # Sun and fog scores (use current values)
        sun_score = get_sun_score(safe_get(weather_codes, current_idx))
        fog_score = get_fog_score(safe_get(visibility_m, current_idx))
        temp_now = round(safe_get(temps_c, current_idx, 0))

        print(f"✓ Weather Success:")
        print(f"  Wind: Now={wind_now}kts, +1h={wind_plus1}kts, +2h={wind_plus2}kts, +3h={wind_plus3}kts, Tmr@9={wind_tmr}kts")
        print(f"  Precipitation (next 2h): {precip_next2h}mm")
        print(f"  Visibility: {safe_get(visibility_m, current_idx)}m → Fog Score: {fog_score}")
        print(f"  Weather Code: {safe_get(weather_codes, current_idx)} → Sun Score: {sun_score}")
        
        # Return: [Precip, WindNow, Wind+1, Wind+2, Wind+3, WindTmr@9, Sun, Fog]
        return [
            precip_next2h,
            wind_now,
            wind_plus1,
            wind_plus2,
            wind_plus3,
            wind_tmr,
            sun_score,
            fog_score,
            temp_now
        ]
        
    except Exception as e:
        print(f"✗ Weather Error: {e}")
        import traceback
        traceback.print_exc()
        return [0] * 8

def main():
    """Main execution function"""
    print("=" * 70)
    print("Garmin Rowing Data Fetcher - Nijmegen")
    print("Using Open-Meteo (KNMI HARMONIE AROME) + RWS Lobith")
    print("=" * 70)
    
    # Get current time in Amsterdam timezone
    tz = pytz.timezone('Europe/Amsterdam')
    now = datetime.now(tz)
    print(f"Fetch time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
    
    # Fetch data
    w_now, w_tmr = fetch_rws_data(now)
    weather_data = fetch_weather_data(now)
    
    # Pack into array: [Timestamp, WaterNow, WaterTmr, ...Weather data...]
    packed = [int(now.timestamp()), w_now, w_tmr] + weather_data
    
    # Output
    print("\n" + "=" * 70)
    print("FINAL PACKED JSON")
    print("=" * 70)
    print(json.dumps(packed))
    print("\nFormat: [Timestamp, WaterNow, WaterTmr, Precip2h, WindNow, Wind+1, Wind+2, Wind+3, WindTmr@9, Sun, Fog, Temp]")
    print(f"Array length: {len(packed)} (expected: 12)")
    
    # Save to file
    with open("data.json", "w") as f:
        json.dump(packed, f)
    print("\n✓ Saved to data.json")

if __name__ == "__main__":
    main()
