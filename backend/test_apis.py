"""
Simple test script to verify fetch_data.py works locally
Tests both RWS and Open-Meteo APIs (no API keys needed!)
"""

import requests
import json
from datetime import datetime
import pytz

# Quick test of Open-Meteo
def test_open_meteo():
    print("=== Testing Open-Meteo (KNMI HARMONIE) ===")
    url = "https://api.open-meteo.com/v1/forecast?latitude=51.847683&longitude=5.862825&hourly=visibility,precipitation,weather_code,wind_speed_10m&models=knmi_harmonie_arome_netherlands&timezone=auto&forecast_days=3"
    
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        print(f"✓ Response received: {len(str(data))} bytes")
        print(f"✓ Latitude: {data['latitude']}")
        print(f"✓ Timezone: {data['timezone']}")
        print(f"✓ Hours of data: {len(data['hourly']['time'])}")
        
        # Show first 3 hours
        print("\nFirst 3 hours of forecast:")
        for i in range(min(3, len(data['hourly']['time']))):
            print(f"  {data['hourly']['time'][i]}")
            print(f"    Wind: {data['hourly']['wind_speed_10m'][i]} km/h")
            print(f"    Precip: {data['hourly']['precipitation'][i]} mm")
            print(f"    Weather code: {data['hourly']['weather_code'][i]}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

# Quick test of RWS
def test_rws():
    print("\n=== Testing RWS (Lobith Water Levels) ===")
    url = "https://waterinfo.rws.nl/api/chart/get?locationCodes=Lobith(LOBI)&values=-48,48&mapType=waterhoogte"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/csv"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        
        lines = r.text.split('\n')
        print(f"✓ Response received: {len(r.text)} bytes")
        print(f"✓ CSV has {len(lines)} lines")
        print(f"✓ Header: {lines[0][:100]}...")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("Quick API Test - No API Keys Required!")
    print("=" * 70)
    print()
    
    meteo_ok = test_open_meteo()
    rws_ok = test_rws()
    
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print(f"Open-Meteo API: {'✓ WORKING' if meteo_ok else '✗ FAILED'}")
    print(f"RWS API: {'✓ WORKING' if rws_ok else '✗ FAILED'}")
    
    if meteo_ok and rws_ok:
        print("\n✓ Both APIs working! Run 'python3 fetch_data.py' for full output.")
    else:
        print("\n✗ Some APIs failed. Check your internet connection.")
