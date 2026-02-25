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
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, request, send_file, jsonify

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
    reader = _get_geoip_reader()
    if reader is None:
        return "XX"
    try:
        response = reader.country(ip)
        return response.country.iso_code or "XX"
    except Exception:
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
    """Log an analytics entry for this request if not recently seen."""
    now = time.time()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_salt = _get_daily_salt(today)
    user_hash = _hash_user(ip, daily_salt)

    # Dedup check
    if user_hash in _recent_users and (now - _recent_users[user_hash]) < DEDUP_INTERVAL:
        return  # Already logged recently

    # Update dedup cache
    _recent_users[user_hash] = now

    # Periodic cleanup of old entries
    if len(_recent_users) > 1000:
        _cleanup_dedup_cache()

    # Country lookup
    country = _lookup_country(ip)

    # Append to daily JSONL file
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = ANALYTICS_DIR / f"{today}.jsonl"

    entry = {
        "ts": int(now),
        "uid": user_hash,
        "country": country,
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


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


@app.route("/health")
def health():
    """Simple health check endpoint."""
    return jsonify({
        "status": "ok",
        "geoip": GEOIP_AVAILABLE and GEOIP_DB_PATH.exists(),
        "data_json": DATA_JSON_PATH.exists(),
    })


if __name__ == "__main__":
    print(f"[analytics] Data JSON path: {DATA_JSON_PATH}")
    print(f"[analytics] Analytics dir: {ANALYTICS_DIR}")
    print(f"[analytics] GeoIP available: {GEOIP_AVAILABLE and GEOIP_DB_PATH.exists()}")
    app.run(host="127.0.0.1", port=8001, debug=True)
