"""
Lightweight zero-dependency task scheduler for Docker environments.
Runs `fetch_data.py` every 15 minutes and `analytics_report.py` daily at 03:00.
Logs output cleanly to stdout so `docker logs` captures everything.
"""

import time
import subprocess
from datetime import datetime
import sys

def run_cmd(name, cmd):
    print(f"\n--- [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Executing: {name} ---", flush=True)
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)
        print(result.stdout, flush=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR running {name}:\n{e.stderr}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    print("🚀 Starting Docker Python Scheduler...", flush=True)
    
    last_fetch_time = 0
    last_report_time = 0

    # Run initial fetch immediately on startup
    print("Initial fetch running now...")
    run_cmd("fetch_data", "python backend/fetch_data.py")
    last_fetch_time = time.time()

    while True:
        now = time.time()
        dt = datetime.now()

        # Run fetch_data every 15 mins (900 seconds)
        if now - last_fetch_time >= 900:
            run_cmd("fetch_data", "python backend/fetch_data.py")
            last_fetch_time = time.time()

        # Run analytics report daily around 03:00 (ensure it runs once per day)
        # 86000 seconds is approx 24 hours minus a small buffer
        if dt.hour == 3 and dt.minute < 5 and (now - last_report_time) > 86000:
            run_cmd("analytics_report", "python backend/analytics_report.py --days 90")
            last_report_time = time.time()

        # Sleep for 60 seconds before checking again
        time.sleep(60)
