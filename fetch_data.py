import requests
import json
import os
from datetime import datetime, timedelta
import pytz
import xarray as xr
import io

# --- CONFIGURATION ---
# Nijmegen Coordinates (approx)
LAT = 51.84
LON = 5.86

# Windfinder-ish Color Logic (Knots)
# Returns integer code: 0=Purple, 1=Blue, 2=Cyan, 3=Green, 4=DarkGreen, 5=Yellow, 6=Orange, 7=Red
def get_wind_color(knots):
    if knots < 6: return 0    # Purple
    if knots < 13: return 1   # Blue
    if knots < 25: return 2   # Cyan
    if knots < 35: return 3   # Green
    if knots < 43: return 4   # Dark Green
    if knots < 50: return 5   # Yellow
    if knots < 60: return 6   # Orange
    return 7                  # Red

# Cloud Cover (0-1 or 0-8 scale) to Icon ID
# 0=Clear, 1=Partly, 2=Cloudy, 3=Overcast
def get_sun_icon(cloud_fraction_0_1):
    if cloud_fraction_0_1 < 0.2: return 0
    if cloud_fraction_0_1 < 0.6: return 1
    if cloud_fraction_0_1 < 0.9: return 2
    return 3

# Visibility (meters) to Fog Scale 0-5
# 0 = No Fog (>10km), 5 = Thick Fog (<200m)
def get_fog_score(visibility_m):
    if visibility_m > 10000: return 0
    if visibility_m > 4000: return 1
    if visibility_m > 2000: return 2
    if visibility_m > 1000: return 3
    if visibility_m > 200: return 4
    return 5

def mps_to_knots(mps):
    return mps * 1.94384

def main():
    api_key = os.environ.get('KNMI_API_KEY')
    ams_tz = pytz.timezone('Europe/Amsterdam')
    now = datetime.now(ams_tz)
    
    # ---------------------------------------------------------
    # 1. FETCH RWS WATER DATA (LOBITH)
    # ---------------------------------------------------------
    water_now = 0
    water_tmr_9 = 0
    
    try:
        # RWS API for Lobith (Code: LOB)
        # Using the "Waterhoogte" (Height) endpoint
        start_date = now.strftime('%Y-%m-%dT%H:%M:%S') + '+01:00'
        end_date = (now + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%S') + '+01:00'
        
        # Locatie: Lobith (Code LOB), Grootheid: Waterhoogte (Code WATHTE)
        rws_url = "https://waterinfo.rws.nl/api/point/values"
        params = {
            "locationCode": "LOB",
            "parameterCode": "WATHTE",
            "startTime": start_date,
            "endTime": end_date
        }
        
        r = requests.get(rws_url, params=params)
        data = r.json()
        
        # Find current measurement
        measurements = [d for d in data.get('values', [])]
        if measurements:
            # Sort by time to get latest
            latest = measurements[-1] 
            water_now = int(latest['value'])
            
            # Find prediction for tomorrow 9:00
            tmr_9 = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
            # Find closest value in list
            closest_diff = float('inf')
            for m in measurements:
                m_time = datetime.fromisoformat(m['dateTime'].replace('Z', '+00:00'))
                diff = abs((m_time - tmr_9).total_seconds())
                if diff < closest_diff:
                    closest_diff = diff
                    water_tmr_9 = int(m['value'])
                    
    except Exception as e:
        print(f"RWS Error: {e}")

    # ---------------------------------------------------------
    # 2. FETCH KNMI WEATHER DATA
    # ---------------------------------------------------------
    # We use the Harmonie Arome Model (High Res) via Open Data API
    # Since parsing NetCDF is heavy, we'll try to get the latest file
    
    # Placeholder values in case API fails
    wind_now = 0
    wind_now_col = 0
    wind_next_1 = 0
    wind_next_1_col = 0
    wind_next_2 = 0
    wind_next_2_col = 0
    wind_tmr_9 = 0
    wind_tmr_9_col = 0
    precip_2h = 0
    sun_icon = 0
    fog_score = 0
    
    try:
        # KNMI Open Data API endpoint for Harmonie Arome (files)
        # We list files, pick the latest, download, and read with Xarray
        base_url = "https://api.dataplatform.knmi.nl/open-data/v1/datasets/harmonie_arome_cy43_p1/versions/1.0/files"
        headers = {"Authorization": api_key}
        
        # Get list of recent files
        list_r = requests.get(f"{base_url}?maxKeys=5&orderBy=lastModified&sorting=desc", headers=headers)
        files = list_r.json().get('files', [])
        
        if files:
            latest_file = files[0]['filename']
            # Download URL
            file_url = f"{base_url}/{latest_file}/url"
            dl_r = requests.get(file_url, headers=headers)
            real_dl_url = dl_r.json().get('temporaryDownloadUrl')
            
            # Download binary content
            nc_data = requests.get(real_dl_url).content
            
            # Open with xarray
            ds = xr.open_dataset(io.BytesIO(nc_data), engine='h5netcdf')
            
            # Select Point (Nearest to Nijmegen)
            point_data = ds.sel(x=LON, y=LAT, method='nearest')
            
            # Extract Time Series
            times = point_data.time.values
            
            # Helper to find index of a specific time
            def get_val_at_time(target_dt, param_name):
                # Convert target to numpy datetime64
                target_np = np_dt = target_dt.astimezone(pytz.utc).replace(tzinfo=None)
                # Find nearest time index
                # (Simple loop for robustness)
                nearest_idx = 0
                min_diff = float('inf')
                for i, t in enumerate(times):
                    # Convert t to standard python datetime if needed, usually numpy64
                    # Compare in seconds
                    ts = (t - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')
                    target_ts = target_np.timestamp()
                    diff = abs(ts - target_ts)
                    if diff < min_diff:
                        min_diff = diff
                        nearest_idx = i
                return float(point_data[param_name].isel(time=nearest_idx).values)

            # --- Extract Variables ---
            # KNMI parameter names vary, standard Harmonie usually has:
            # 'wind_speed_10m' or similar. 
            # Note: Checking standard CF conventions for Harmonie
            
            # Wind Speed (often 'ff' or 'wind_speed') - check your dataset specifics
            # Assuming 'ff' for wind speed in m/s based on common KNMI headers
            # If failing, print(ds.data_vars) to debug in logs
            w_spd = 'wind_speed_10m' if 'wind_speed_10m' in ds else 'ff'
            precip = 'precipitation_flux' if 'precipitation_flux' in ds else 'pr' # kg/m2/s
            clouds = 'cloud_area_fraction' if 'cloud_area_fraction' in ds else 'clt'
            vis = 'visibility' if 'visibility' in ds else 'vis'

            # 1. Wind (Current, +1, +2, Tmr 9:00)
            w_now_mps = get_val_at_time(now, w_spd)
            w_n1_mps = get_val_at_time(now + timedelta(hours=1), w_spd)
            w_n2_mps = get_val_at_time(now + timedelta(hours=2), w_spd)
            tmr_9 = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
            w_tmr_mps = get_val_at_time(tmr_9, w_spd)
            
            wind_now = int(round(mps_to_knots(w_now_mps)))
            wind_now_col = get_wind_color(wind_now)
            
            w_n1 = int(round(mps_to_knots(w_n1_mps)))
            wind_next_1 = w_n1
            wind_next_1_col = get_wind_color(w_n1)
            
            w_n2 = int(round(mps_to_knots(w_n2_mps)))
            wind_next_2 = w_n2
            wind_next_2_col = get_wind_color(w_n2)
            
            w_tmr = int(round(mps_to_knots(w_tmr_mps)))
            wind_tmr_9 = w_tmr
            wind_tmr_9_col = get_wind_color(w_tmr)
            
            # 2. Precipitation (Sum next 2h)
            # KNMI often gives flux (kg/m2/s) or accumulated. 
            # If flux: sum * 3600. If accumulated, take diff.
            # Simplified: Check probability or simple flux. 
            # Let's assume flux for this script.
            p_now = get_val_at_time(now, precip)
            p_1h = get_val_at_time(now + timedelta(hours=1), precip)
            # convert kg/m2/s to mm/h -> value * 3600
            precip_mm = (p_now + p_1h) * 3600
            precip_2h = round(precip_mm, 1)

            # 3. Sun/Fog (Next 2 hours average)
            c_now = get_val_at_time(now, clouds) # 0-1
            sun_icon = get_sun_icon(c_now)
            
            v_now = get_val_at_time(now, vis) # meters
            fog_score = get_fog_score(v_now)

    except Exception as e:
        print(f"KNMI Error: {e}")
        # import traceback
        # traceback.print_exc()

    # ---------------------------------------------------------
    # 3. PACK DATA
    # ---------------------------------------------------------
    # Unix Timestamp for stale check
    ts = int(now.timestamp())
    
    # ARRAY MAPPING:
    # 0: Timestamp
    # 1: Water Now (cm)
    # 2: Water Tomorrow 9:00 (cm)
    # 3: Precip next 2h (mm)
    # 4: Wind Now (kts)
    # 5: Wind Now Color
    # 6: Wind +1h (kts)
    # 7: Wind +1h Color
    # 8: Wind +2h (kts)
    # 9: Wind +2h Color
    # 10: Wind Tomorrow 9:00 (kts)
    # 11: Wind Tomorrow 9:00 Color
    # 12: Sun Icon
    # 13: Fog Score
    
    packed = [
        ts,
        water_now, water_tmr_9,
        precip_2h,
        wind_now, wind_now_col,
        wind_next_1, wind_next_1_col,
        wind_next_2, wind_next_2_col,
        wind_tmr_9, wind_tmr_9_col,
        sun_icon,
        fog_score
    ]
    
    # Save to JSON
    with open('data.json', 'w') as f:
        json.dump(packed, f)
        
    print("Successfully packed data:", packed)

if __name__ == "__main__":
    import numpy as np # Helper for datetime conversion in main
    main()
