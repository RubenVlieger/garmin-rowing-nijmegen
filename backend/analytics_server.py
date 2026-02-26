"""
Analytics Server for Garmin Rowing Watchface
=============================================
Lightweight Flask app that serves data.json while logging anonymous analytics.

- Logs a hashed user ID (SHA-256 of IP + daily salt, truncated to 16 chars)
- Looks up country from IP using GeoLite2-Country offline database
- Deduplicates: skips logging if same user was logged within the last hour
- Stores daily JSONL log files in analytics/ directory

Run with gunicorn:
    gunicorn -b 127.0.0.1:8001 analytics_server:app
"""

import hashlib
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, request, send_file, jsonify

try:
    from analytics_report import generate_report
except ImportError:
    generate_report = None


# Optional: GeoIP2 for country lookup
try:
    import geoip2.database
    GEOIP_AVAILABLE = True
except ImportError:
    GEOIP_AVAILABLE = False

# --- Configuration ---
BASE_DIR = Path(__file__).parent.resolve()
DATA_JSON_PATH = BASE_DIR.parent / "data.json"
ANALYTICS_DIR = BASE_DIR / "analytics"
GEOIP_DB_PATH = BASE_DIR / "GeoLite2-Country.mmdb"
SUGGESTIONS_DB_PATH = BASE_DIR / "suggestions.db"
USERS_DB_PATH = BASE_DIR / "users.db"
SUMMARY_JSON_PATH = ANALYTICS_DIR / "summary.json"

# How often the same user can be logged (seconds) — matches Garmin's hourly interval
DEDUP_INTERVAL = 3500  # slightly less than 1 hour to avoid edge cases

app = Flask(__name__)

# --- In-memory dedup cache: {user_hash: last_log_timestamp} ---
_recent_users = {}

# --- GeoIP Reader (loaded once) ---
_geoip_reader = None


def _get_geoip_reader():
    """Lazy-load the GeoIP reader."""
    global _geoip_reader
    if _geoip_reader is None and GEOIP_AVAILABLE and GEOIP_DB_PATH.exists():
        try:
            _geoip_reader = geoip2.database.Reader(str(GEOIP_DB_PATH))
        except Exception as e:
            print(f"[analytics] Failed to load GeoIP database: {e}")
    return _geoip_reader


def _get_daily_salt(date_str: str) -> str:
    """Get or create a daily salt for hashing. Stored in analytics/.salt_YYYY-MM-DD"""
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    salt_file = ANALYTICS_DIR / f".salt_{date_str}"

    if salt_file.exists():
        return salt_file.read_text().strip()

    salt = secrets.token_hex(16)
    salt_file.write_text(salt)
    return salt


def _hash_user(ip: str, daily_salt: str) -> str:
    """Create a truncated SHA-256 hash of IP + daily salt."""
    raw = f"{ip}:{daily_salt}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _lookup_country(ip: str) -> str:
    """Look up the country code for an IP address. Returns 'XX' on failure."""
    # Private/local IPs can't be geolocated
    private_prefixes = ("127.", "10.", "192.168.", "172.16.", "172.17.",
                        "172.18.", "172.19.", "172.2", "172.3", "0.", "::1")
    if ip.startswith(private_prefixes):
        print(f"[geoip] Private/internal IP detected: {ip} → XX")
        return "XX"

    reader = _get_geoip_reader()
    if reader is None:
        print(f"[geoip] GeoIP reader unavailable for IP: {ip} → XX")
        return "XX"
    try:
        response = reader.country(ip)
        code = response.country.iso_code or "XX"
        print(f"[geoip] {ip} → {code}")
        return code
    except Exception as e:
        print(f"[geoip] Lookup failed for {ip}: {e} → XX")
        return "XX"


def _get_client_ip() -> str:
    """Extract client IP from X-Forwarded-For header (set by nginx) or fall back to remote_addr."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs; the first is the client
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "0.0.0.0"


def _cleanup_dedup_cache():
    """Remove entries older than DEDUP_INTERVAL from the in-memory cache."""
    now = time.time()
    expired = [uid for uid, ts in _recent_users.items() if now - ts > DEDUP_INTERVAL]
    for uid in expired:
        del _recent_users[uid]


def _log_analytics(ip: str):
    now = time.time()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # 1. Grab the UID passed from the Garmin watch
    device_uid = request.args.get("uid")
    is_real_uid = bool(device_uid)
    
    # Fallback to IP hashing ONLY if it's accessed via a normal web browser
    if not device_uid:
        daily_salt = _get_daily_salt(today)
        device_uid = _hash_user(ip, daily_salt)
    
    # 2. Use the device_uid for your dedup check
    if device_uid in _recent_users and (now - _recent_users[device_uid]) < DEDUP_INTERVAL:
        return 
        
    _recent_users[device_uid] = now

    if len(_recent_users) > 1000:
        _cleanup_dedup_cache()

    # Country lookup
    country = _lookup_country(ip)

    # Append to daily JSONL file
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = ANALYTICS_DIR / f"{today}.jsonl"

    entry = {
        "ts": int(now),
        "uid": device_uid,
        "country": country
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Log to unique users db only if it's a real device UID from garmin watch
    if is_real_uid:
        try:
            conn = sqlite3.connect(str(USERS_DB_PATH))
            conn.execute("INSERT OR IGNORE INTO unique_users (uid) VALUES (?)", (device_uid,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[analytics] Error saving real user id: {e}")



# --- Suggestions Database ---

def _init_suggestions_db():
    """Initialize the SQLite suggestions database."""
    conn = sqlite3.connect(str(SUGGESTIONS_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            suggestion TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


# Initialize DB on import
_init_suggestions_db()

def _init_users_db():
    """Initialize the SQLite unique users database."""
    conn = sqlite3.connect(str(USERS_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS unique_users (
            uid TEXT PRIMARY KEY,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

_init_users_db()


# --- Routes ---

@app.route("/data.json")
def serve_data():
    """Serve data.json and log analytics."""
    # Log analytics (non-blocking, best-effort)
    try:
        ip = _get_client_ip()
        _log_analytics(ip)
    except Exception as e:
        # Never let analytics failures break data serving
        print(f"[analytics] Error logging: {e}")

    # Serve data.json
    if DATA_JSON_PATH.exists():
        response = send_file(
            str(DATA_JSON_PATH),
            mimetype="application/json",
        )
        # Add CORS header to match existing nginx config
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Cache-Control"] = "no-cache"
        return response
    else:
        return jsonify({"error": "data.json not found"}), 404


@app.route("/api/summary")
def api_summary():
    """Serve the analytics summary JSON, regenerating it on the fly."""
    if generate_report:
        try:
            generate_report(max_days=30)
        except Exception as e:
            print(f"[analytics] Error generating summary report: {e}")
            
    if SUMMARY_JSON_PATH.exists():
        try:
            with open(SUMMARY_JSON_PATH, "r") as f:
                data = json.load(f)
            return jsonify(data)
        except (json.JSONDecodeError, IOError) as e:
            return jsonify({"error": f"Failed to read summary: {e}"}), 500
    else:
        # If no summary.json exists yet, generate a live summary from JSONL files
        return _live_summary()


def _live_summary():
    """Generate a summary on the fly from JSONL files (fallback if report hasn't run)."""
    from collections import defaultdict
    summary = {}

    if not ANALYTICS_DIR.exists():
        return jsonify({})

    for log_file in sorted(ANALYTICS_DIR.glob("*.jsonl")):
        date_str = log_file.stem
        unique_users = set()
        countries = defaultdict(int)

        with open(log_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    uid = entry.get("uid", "")
                    country = entry.get("country", "XX")
                    if uid and uid not in unique_users:
                        unique_users.add(uid)
                        countries[country] += 1
                except json.JSONDecodeError:
                    continue

        summary[date_str] = {
            "unique_users": len(unique_users),
            "countries": dict(sorted(countries.items(), key=lambda x: -x[1])),
        }

    return jsonify(summary)

@app.route("/api/total_users")
def api_total_users():
    """Return the total number of unique users tracked in the users.db."""
    try:
        conn = sqlite3.connect(str(USERS_DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM unique_users")
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({"total_users": count})
    except Exception as e:
        print(f"[analytics] Error retrieving total unique users: {e}")
        return jsonify({"total_users": 0}), 500


@app.route("/api/suggestions", methods=["POST"])
def api_submit_suggestion():
    """Save a feature suggestion to the database."""
    data = request.get_json(silent=True)
    if not data or not data.get("suggestion", "").strip():
        return jsonify({"error": "Suggestion text is required"}), 400

    name = (data.get("name") or "").strip()[:100]  # Limit name length
    suggestion = data["suggestion"].strip()[:2000]  # Limit suggestion length

    try:
        conn = sqlite3.connect(str(SUGGESTIONS_DB_PATH))
        conn.execute(
            "INSERT INTO suggestions (name, suggestion) VALUES (?, ?)",
            (name or None, suggestion),
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"}), 201
    except Exception as e:
        print(f"[suggestions] Error saving: {e}")
        return jsonify({"error": "Failed to save suggestion"}), 500


@app.route("/health")
def health():
    """Simple health check endpoint."""
    return jsonify({
        "status": "ok",
        "geoip": GEOIP_AVAILABLE and GEOIP_DB_PATH.exists(),
        "data_json": DATA_JSON_PATH.exists(),
        "suggestions_db": SUGGESTIONS_DB_PATH.exists(),
    })


@app.route("/debug/ip")
def debug_ip():
    """Debug: show what IP Flask sees for this request."""
    ip = _get_client_ip()
    country = _lookup_country(ip)
    return jsonify({
        "raw_ip": ip,
        "country": country,
        "x_forwarded_for": request.headers.get("X-Forwarded-For", None),
        "remote_addr": request.remote_addr,
        "geoip_available": GEOIP_AVAILABLE and GEOIP_DB_PATH.exists(),
    })


if __name__ == "__main__":
    print(f"[analytics] Data JSON path: {DATA_JSON_PATH}")
    print(f"[analytics] Analytics dir: {ANALYTICS_DIR}")
    print(f"[analytics] GeoIP available: {GEOIP_AVAILABLE and GEOIP_DB_PATH.exists()}")
    print(f"[analytics] Suggestions DB: {SUGGESTIONS_DB_PATH}")
    app.run(host="127.0.0.1", port=8001, debug=True)

