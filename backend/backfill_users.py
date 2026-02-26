import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
ANALYTICS_DIR = BASE_DIR / "analytics"
USERS_DB_PATH = BASE_DIR / "users.db"

def backfill():
    print(f"Initializing database at {USERS_DB_PATH} (if not exists)...")
    conn = sqlite3.connect(str(USERS_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS unique_users (
            uid TEXT PRIMARY KEY,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    if not ANALYTICS_DIR.exists():
        print(f"No analytics dir found at {ANALYTICS_DIR}")
        return

    jsonl_files = sorted(ANALYTICS_DIR.glob("*.jsonl"))
    print(f"Found {len(jsonl_files)} log files in {ANALYTICS_DIR}.")

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM unique_users")
    count_before = cursor.fetchone()[0]
    print(f"Users in DB before backfill: {count_before}")

    scanned = 0
    skipped_16 = 0

    for fpath in jsonl_files:
        with open(fpath, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    uid = data.get("uid")
                    if uid:
                        scanned += 1
                        # Skip if length == 16 (assumed to be v1.4 hashed IP)
                        if len(uid) == 16:
                            skipped_16 += 1
                            continue
                        
                        # Use the logged timestamp for first_seen if available
                        ts = data.get("ts")
                        
                        if ts:
                            conn.execute(
                                "INSERT OR IGNORE INTO unique_users (uid, first_seen) VALUES (?, datetime(?, 'unixepoch'))", 
                                (uid, ts)
                            )
                        else:
                            conn.execute(
                                "INSERT OR IGNORE INTO unique_users (uid) VALUES (?)", 
                                (uid,)
                            )
                except json.JSONDecodeError:
                    continue

    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM unique_users")
    count_after = cursor.fetchone()[0]
    conn.close()

    inserted = count_after - count_before
    print(f"\n--- Backfill Summary ---")
    print(f"Scanned {scanned} valid UID entries.")
    print(f"Skipped {skipped_16} entries with length 16 (v1.4 hashed IPs).")
    print(f"Inserted {inserted} new distinct genuine device UIDs.")
    print(f"Total Unique Users in DB now: {count_after}")

if __name__ == "__main__":
    backfill()
